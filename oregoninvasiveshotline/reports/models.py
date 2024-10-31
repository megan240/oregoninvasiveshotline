import posixpath
import logging
import os

from django.dispatch import receiver
from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.urls import reverse
from django.conf import settings

from oregoninvasiveshotline.utils.settings import get_setting
from oregoninvasiveshotline.utils.images import generate_thumbnail
from oregoninvasiveshotline.visibility import Visibility
from oregoninvasiveshotline.images.models import Image
from oregoninvasiveshotline.users.models import User

from .utils import generate_icon, icon_file_name

log = logging.getLogger(__name__)


class Report(models.Model):
    """
    TBD
    """
    class Meta:
        db_table = 'report'
        ordering = ['-created_on']

    report_id = models.AutoField(primary_key=True)
    # It may seem odd to have FKs to the species AND category, but in the case
    # where the user doesn't know what species it is, we fall back to just a
    # category (with the reported_species field NULL'd out)
    reported_category = models.ForeignKey("species.Category", on_delete=models.CASCADE)
    reported_species = models.ForeignKey("species.Species", null=True, default=None, related_name="+", on_delete=models.SET_NULL)

    description = models.TextField(verbose_name="Please provide a description of your find")
    location = models.TextField(
        verbose_name="Please provide a description of the area where species was found",
        help_text="""
            For example name the road, trail or specific landmarks
            near the site whether the species was found. Describe the geographic
            location, such as in a ditch, on a hillside or in a streambed. If you
            happen to have taken GPS coordinates, enter them here.
        """
    )
    has_specimen = models.BooleanField(default=False, verbose_name="Do you have a physical specimen?")

    point = models.PointField(srid=4326)
    county = models.ForeignKey('counties.County', null=True, on_delete=models.SET_NULL)
    city = models.ForeignKey('cities.City', null=True, on_delete=models.SET_NULL)

    created_by = models.ForeignKey("users.User", related_name="reports", on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    claimed_by = models.ForeignKey("users.User", null=True, default=None, related_name="claimed_reports", on_delete=models.SET_NULL)

    # these are copied over from the original site
    edrr_status = models.IntegerField(verbose_name="EDRR Status", choices=[
        (None, '',),
        (0, 'No Response/Action Required',),
        (1, 'Local expert notified',),
        (2, 'Population assessed',),
        (3, 'Population treated',),
        (4, 'Ongoing monitoring',),
        (5, 'Controlled at site'),
    ], default=None, null=True, blank=True)

    # the actual species confirmed by an expert
    actual_species = models.ForeignKey("species.Species", null=True, default=None, related_name="reports", on_delete=models.SET_NULL)

    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False, help_text="This report can be viewed by the public")

    @property
    def title(self):
        return self.species.title if self.species else self.category.name

    @property
    def icon_color(self):
        species = self.species
        return settings.ICON_DEFAULT_COLOR if species is None else species.severity.color

    @property
    def icon_file_name(self):
        """Get base file name for this report's icon.

        This is used by :meth:`icon_path` and :meth:`icon_url` to
        generate icon file system paths and URLs; generally, you'd use
        one of those instead of using this directly.

        """
        return icon_file_name(self.category.icon, self.icon_color)

    @property
    def icon_path(self):
        """Path to (generated) icon for this report."""
        return os.path.join(settings.MEDIA_ROOT, settings.ICON_DIR, self.icon_file_name)

    @property
    def icon_url(self):
        """Get icon URL for this report."""
        return posixpath.join(settings.MEDIA_URL, settings.ICON_DIR, self.icon_file_name)

    def generate_icon(self, force=False):
        """Generate a map-style icon for this Report.

        Normally, a report icon will be generated only if it doesn't
        already exist on disk, but generation can be ``force``d.

        When a report is saved, its icon will be re-generated if
        necessary.

        """
        icon_path = self.icon_path
        if force or not os.path.exists(icon_path):
            inner_icon_path = self.category.icon and self.category.icon.path
            icon = generate_icon(icon_path, inner_icon_path, self.icon_color)
            return icon

    @property
    def image_url(self):
        """Get URL for "first" public image attached to this report.

        If the report has at least one public image, the thumbnail URL
        for the newest image will be returned. Otherwise, the report's
        comments are checked for public images.

        If the thumbnail for the selected image doesn't exist, it will
        be created as a side effect.

        If no image is found, ``None`` will be returned.

        """
        # Try to get a directly-attached image first
        q = Image.objects.filter(report=self)
        q = q.filter(visibility=Visibility.PUBLIC).order_by('-created_on')
        image = q.first()

        if image is None:
            # Fall back to images attached to this report's comments
            q = Image.objects.filter(comment__in=self.comment_set.values_list('pk', flat=True))
            q = q.filter(visibility=Visibility.PUBLIC).order_by('-created_on')
            image = q.first()

        if image is None:
            return None

        sub_dir = 'generated_thumbnails'
        output_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
        media_url = posixpath.join(settings.MEDIA_URL, sub_dir)

        file_name = '{image.pk}.png'.format(image=image)
        output_path = os.path.join(output_dir, file_name)

        if not os.path.exists(output_path):
            generate_thumbnail(image.image.path, output_path, width=64, height=64)
        return posixpath.join(media_url, file_name)

    @property
    def species(self):
        """Return actual species if set; fall back to reported species."""
        return self.actual_species or self.reported_species

    @property
    def category(self):
        """Return actual category if set; fall back to reported category."""
        return self.actual_species.category if self.actual_species else self.reported_category

    @property
    def is_misidentified(self):
        """Is reported species different from actual species?"""
        if self.reported_species and self.actual_species:
            return self.reported_species != self.actual_species
        return False

    def get_absolute_url(self):
        return reverse('reports-detail', args=(self.pk,))

    def __str__(self):
        return 'Report: {0.title}'.format(self)


@receiver([post_save], sender=Report)
def receiver__generate_icon(sender, instance, **kwargs):
    """
    Create or update icon for Report on save.
    """
    instance.generate_icon()


class Invite(models.Model):
    """An invitation to review a report.

    Arbitrary people can be invited (via email) to review and leave
    comments on a report.
    """
    class Meta:
        db_table = 'invite'

    invite_id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey('users.User', related_name='+', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE)

    # The invitee
    user = models.ForeignKey('users.User', related_name='invites', on_delete=models.CASCADE)
