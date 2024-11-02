from collections import OrderedDict
import functools
import itertools
import posixpath
import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from oregoninvasiveshotline.utils.urls import safe_redirect
from oregoninvasiveshotline.utils.db import will_be_deleted_with
from oregoninvasiveshotline.comments.forms import CommentForm
from oregoninvasiveshotline.comments.models import Comment
from oregoninvasiveshotline.comments.perms import can_create_comment
from oregoninvasiveshotline.images.forms import get_image_formset
from oregoninvasiveshotline.images.models import Image
from oregoninvasiveshotline.species.models import Category, Severity, category_id_to_species_id_json
from oregoninvasiveshotline.users.utils import get_tab_counts

from .forms import InviteForm, ManagementForm, ReportForm, ReportSearchForm
from .models import Invite, Report
from .perms import can_manage_report, can_view_private_report, can_claim_report, permissions
from .serializers import ReportSerializer
from .utils import icon_file_name


def list_(request):
    params = request.GET
    user = request.user
    report_ids = request.session.get('report_ids', [])

    form = ReportSearchForm(params, user=user, report_ids=report_ids)
    reports = Report.objects.all()
    if form.is_valid():
        reports = form.search(reports)

    # Handle the case where they want to export the reports
    # XXX: Why isn't this a separate view?
    export_format = params.get('export')
    if user.is_active and export_format in ('kml', 'csv'):
        return _export(reports=reports, format=export_format)

    # Paginate the results
    paginator = Paginator(reports, settings.ITEMS_PER_PAGE)
    active_page = request.GET.get('page')

    try:
        page = paginator.page(active_page)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    # Serialize and render report data to JSON
    serializer = ReportSerializer(page.object_list, many=True)
    reports = serializer.data

    template_name = 'list' if user.is_active else 'list_public'
    template = 'reports/{name}.html'.format(name=template_name)

    tab = params.get('tabs') or 'search'
    tab_context = get_tab_counts(user, report_ids)

    subscription_url = reverse('notifications-create')
    subscription_params = request.GET.urlencode()
    if subscription_params:
        subscription_url = '?'.join((subscription_url, subscription_params))
    else:
        subscription_url = None

    context = {
        'reports': reports,
        'page': page,
        'form': form,
        'subscription_url': subscription_url,
        'tab': tab,
    }
    context.update(tab_context)

    return render(request, template, context)


def help(request):
    categories = OrderedDict()
    base_icon_url = posixpath.join(settings.MEDIA_URL, settings.ICON_DIR)
    pairs = itertools.product(Category.objects.all(), Severity.objects.all())
    for category, severity in pairs:
        file_name = icon_file_name(category.icon, severity.color)
        icon_url = posixpath.join(base_icon_url, file_name)
        categories.setdefault(category, []).append({
            'icon_url': icon_url,
            'severity': severity.name
        })
    return render(request, 'reports/help.html', {
        'categories': categories,
    })


def _export(reports, format):
    """
    Returns an HttpResponse containing all the reports in the specified format
    """
    if format == "csv":
        response = HttpResponse("", content_type="text/csv")
        # maps a field name, to a function that gets the data for the field,
        # given a Report object
        fields = OrderedDict([
            ("Report ID", lambda report: report.pk),
            ("Category", lambda report: str(report.category)),
            ("Common Name", lambda report: report.species.name if report.species else ""),
            ("Scientific Name", lambda report: report.species.scientific_name if report.species else ""),
            ("Species Confirmed", lambda report: bool(report.actual_species)),
            ("Reported By", lambda report: str(report.created_by)),
            ("OFPD Trained", lambda report: str(report.created_by.has_completed_ofpd)),
            ("Reported On", lambda report: str(report.created_on)),
            ("Claimed By", lambda report: str(report.claimed_by)),
            ("Description", lambda report: report.description),
            ("Latitude", lambda report: report.point.y),
            ("Longitude", lambda report: report.point.x),
            ("EDRR Status", lambda report: report.edrr_status),
            ("Is Public", lambda report: report.is_public),
            ("Is Archived", lambda report: report.is_archived),
        ])
        writer = csv.DictWriter(response, fields.keys())
        writer.writeheader()
        for report in reports:
            row = {}
            for key, accessor in fields.items():
                row[key] = accessor(report)
            writer.writerow(row)
    elif format == "kml":
        response = HttpResponse(render_to_string("reports/export.kml", {
            "reports": reports
        }), content_type="text/csv")
    else:
        raise ValueError("%s in not a valid format" % format)

    response['Content-Disposition'] = 'attachment; filename="reports.%s"' % format
    return response


def create(request):
    """
    Render the public form for submitting reports
    """
    ImageFormSet = get_image_formset()

    if request.POST:
        form = ReportForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if form.is_valid() and formset.is_valid():
            try:
                report = form.save()
                formset.save(user=report.created_by, fk=report)
                messages.success(request, "Report submitted successfully")
                request.session.setdefault("report_ids", []).append(report.pk)
                request.session.modified = True
                response = redirect("reports-detail", report.pk)
                # the template sets some cookies in JS that we want to clear when
                # the report is submitted. This means the next time they go to this
                # page, the map will be initialized with the defaults
                response.delete_cookie("center", request.get_full_path())
                response.delete_cookie("zoom", request.get_full_path())
                return response
            except ValidationError as e:
                form.add_error(None, e.message)
    else:
        formset = ImageFormSet(queryset=Image.objects.none())
        form = ReportForm()

    return render(request, "reports/create.html", {
        "form": form,
        "category_id_to_species_id": category_id_to_species_id_json(),
        "formset": formset
    })


def detail(request, report_id):
    """
    This is a complex view that handles displaying all the information about a
    Report. It needs to take into account the user's role on the Report to
    determine whether to display the comment form, and which comments to
    display, etc. It also handles the management of the report by the expert
    who claimed it
    """
    report = get_object_or_404(Report, pk=report_id)

    if (report.pk in request.session.get("report_ids", []) and
            report.created_by.is_active and
            report.created_by_id != request.user.pk and
            not request.user.is_active):
        # if the report was created by an active user and they aren't logged in
        # as that user, force them to re-login
        return login_required(lambda request: None)(request)

    if (report.pk in request.session.get("report_ids", []) and
            not report.created_by.is_active and
            report.created_by_id != request.user.pk and
            not request.user.is_active):
        # if the user submitted the report, allow them to masquerade as that
        # user for the life of this request
        request.user = report.created_by

    if not report.is_public:
        if request.user.is_anonymous:
            messages.info(request, "If this is your report, please use the login system below to authenticate yourself.")
            return login_required(lambda request: None)(request)
        elif not can_view_private_report(request.user, report):
            raise PermissionDenied()

    # there are a bunch of forms that can be filled out on this page, by
    # default, they can't be filled out
    comment_form = None
    image_formset = None
    invite_form = None
    management_form = None
    # this tells us which form was filled out since there are many on the page
    submit_flag = request.POST.get("submit_flag")

    # process the comment form only if they are allowed to leave comments
    if can_create_comment(request.user, report):
        ImageFormSet = get_image_formset(user=request.user)
        PartialCommentForm = functools.partial(CommentForm, user=request.user, report=report)

        if request.POST and submit_flag == CommentForm.SUBMIT_FLAG:
            image_formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
            comment_form = PartialCommentForm(request.POST, request.FILES)
            if comment_form.is_valid() and image_formset.is_valid():
                comment = comment_form.save()
                image_formset.save(user=comment.created_by, fk=comment)
                messages.success(request, "Comment Added!")
                if can_claim_report(request.user, report):
                    if report.claimed_by is None:
                        report.claimed_by = request.user
                        report.save()
                        messages.success(request, "Report claimed!")
                return safe_redirect(request, request.get_full_path())

        else:
            comment_form = PartialCommentForm()
            image_formset = ImageFormSet(queryset=Image.objects.none())

    # handle all the management forms
    if can_manage_report(request.user, report):
        # Confirming the report form...
        if request.POST and submit_flag == ManagementForm.SUBMIT_FLAG:
            management_form = ManagementForm(request.POST, instance=report)
            if management_form.is_valid():
                management_form.save()
                messages.success(request, "Updated!")
                return safe_redirect(request, request.get_full_path())
        else:
            management_form = ManagementForm(instance=report)

        # Inviting experts...
        if request.POST and submit_flag == InviteForm.SUBMIT_FLAG:
            invite_form = InviteForm(request.POST)
            if invite_form.is_valid():
                invite_report = invite_form.save(request.user, report)
                message = "%d invited" % (len(invite_report.invited))
                if invite_report.already_invited:
                    message += " (%d already invited)" % len(invite_report.already_invited)
                messages.success(request, message)
                return safe_redirect(request, request.get_full_path())
        else:
            invite_form = InviteForm()

    # filter down the comments based on the user's permissions
    comments = Comment.objects.filter(report=report)
    images = Image.objects.filter(Q(report=report) | Q(comment__report=report))
    if request.user.is_anonymous:
        comments = comments.filter(visibility=Comment.PUBLIC)
        images = images.filter(visibility=Image.PUBLIC)
    elif request.user.is_active or Invite.objects.filter(user=request.user, report=report).exists():
        # no need to filter for these folks
        pass
    else:
        # the logged in user is the person who reported
        comments = comments.filter(Q(visibility=Comment.PUBLIC) | Q(visibility=Comment.PROTECTED))
        images = images.filter(Q(visibility=Image.PUBLIC) | Q(visibility=Image.PROTECTED))

    invites = list(i.user.email for i in Invite.objects.filter(report=report).select_related("user"))

    return render(request, "reports/detail.html", {
        "report": report,
        "comments": comments,
        "images": list(images),
        "category_id_to_species_id": category_id_to_species_id_json(),
        "invites": invites,
        # all the forms
        "image_formset": image_formset,
        "comment_form": comment_form,
        "invite_form": invite_form,
        "management_form": management_form,
    })


@permissions.can_claim_report
def claim(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == "POST" and (report.claimed_by is None or "steal" in request.POST):
        report.claimed_by = request.user
        report.save()
        return redirect("reports-detail", report.pk)

    return render(request, "reports/claim.html", {
        "report": report,
    })


@permissions.can_unclaim_report
def unclaim(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == "POST":
        report.claimed_by = None
        report.save()
        return redirect("reports-detail", report.pk)

    return render(request, "reports/unclaim.html", {
        "report": report,
    })


@permissions.can_delete_report
def delete(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == "POST":
        report.delete()
        messages.success(request, "Report deleted!")
        return redirect("reports-list")

    related_objects = list(will_be_deleted_with(report))

    return render(request, "delete.html", {
        "object": report,
        "will_be_deleted_with": related_objects,
    })
