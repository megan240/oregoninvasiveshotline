from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
import json

from .reports.models import Report
from .reports.serializers import ReportSerializer


User = get_user_model()

# View Reports Page Change 1
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


class HomeView(APIView):

    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'home.html'

    # These options are used in :meth:`get_reports` to fetch the latest
    # N reports. They're class-level options so it's easy to change how
    # many reports are fetched, how they're filtered, and how they're
    # ordered (could be useful in tests, for example).
    show_n_reports = 25
    order_reports_by = '-created_on'
    report_filters = {
        'is_public': True,
    }

    def get(self, request):
        reports = self.get_reports()
        serializer = ReportSerializer(reports, many=True)
        return Response({
            'reports': serializer.data,
        })

    def get_reports(self):
        """Get reports to show on home page.

        Configure which reports are shown using the ``show_n_reports``,
        ``order_reports_by``, and ``report_filters`` class attributes.

        """
        q = Report.objects.filter(**self.report_filters)
        q = q.order_by(self.order_reports_by)
        return q[:self.show_n_reports]


class AdminPanelView(APIView):

    permission_classes = [IsAdminUser]
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'admin_panel.html'

    def get(self, request):
        return Response({})


@csrf_exempt
def update_user_name(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            data = json.loads(request.body)
            print('Received data:', data)
            user.first_name = data.get('first_name', user.first_name)
            user.last_name = data.get('last_name', user.last_name)
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
        except Exception as e:
            print('Error:', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def update_user_email(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            data = json.loads(request.body)
            print('Received data:', data)
            user.email = data.get('email', user.email)
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
        except Exception as e:
            print('Error:', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def update_user_biography(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            data = json.loads(request.body)
            print('Received data:', data)
            user.biography = data.get('biography', user.biography)
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
        except Exception as e:
            print('Error:', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def update_user_affiliations(request, pk):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=pk)
            data = json.loads(request.body)
            print('Received data:', data)
            user.affiliations = data.get('affiliations', user.affiliations)
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})
        except Exception as e:
            print('Error:', str(e))
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# View Reports Page Change 2
@method_decorator(staff_member_required, name='dispatch')
class ViewReportsPageView(TemplateView):
    template_name = 'view_reports_page.html'
