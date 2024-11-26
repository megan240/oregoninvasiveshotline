from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from .comments import views as comments
from .notifications import views as notifications
from .perms import permissions
from .reports import views as reports
from .species import views as species
from .users import views as users
from .views import HomeView, AdminPanelView, update_user_name, update_user_email, update_user_biography, update_user_affiliations
from . import views



urlpatterns = [
    # Redirects for the old site
    url(r'^reports/(?P<report_id>\d+)/?$', lambda request, report_id: redirect('reports-detail', report_id)),
    url(r'^reports/new/?$', lambda request: redirect('reports-create')),
    url(r'^home/search.*$', lambda request: redirect('reports-list')),

    url(r'^$', HomeView.as_view(), name='home'),

    url(r'^admin/', admin.site.urls),
    url(r'^adminpanel/?$', AdminPanelView.as_view(), name='admin-panel'),

    url(r'^categories/create/?$', permissions.is_staff(species.CategoryCreateView.as_view()), name='categories-create'),
    url(r'^categories/delete/(?P<pk>\d+)/?$', permissions.is_staff(species.CategoryDeleteView.as_view()), name='categories-delete'),
    url(r'^categories/detail/(?P<pk>\d+)/?$', permissions.is_staff(species.CategoryDetailView.as_view()), name='categories-detail'),
    url(r'^categories/list/?$', permissions.is_staff(species.CategoryList.as_view()), name='categories-list'),

    url(r'^comments/delete/(?P<comment_id>\d+)/?$', comments.delete, name='comments-delete'),
    url(r'^comments/edit/(?P<comment_id>\d+)/?$', comments.edit, name='comments-edit'),

    url(r'^notifications/all/?$', notifications.admin_list, name='notifications-admin-list'),
    url(r'^notifications/create/?$', notifications.create, name='notifications-create'),
    url(r'^notifications/delete/(?P<subscription_id>\d+)/?$', notifications.delete, name='notifications-delete'),
    url(r'^notifications/edit/(?P<subscription_id>\d+)/?$', notifications.edit, name='notifications-edit'),
    url(r'^notifications/list/?$', notifications.list_, name='notifications-list'),

    url(r'^reports/claim/(?P<report_id>\d+)/?$', reports.claim, name='reports-claim'),
    url(r'^reports/create/?$', reports.create, name='reports-create'),
    url(r'^reports/delete/(?P<report_id>\d+)/?$', reports.delete, name='reports-delete'),
    url(r'^reports/detail/(?P<report_id>\d+)/?$', reports.detail, name='reports-detail'),
    url(r'^reports/help/?$', reports.help, name='reports-help'),
    url(r'^reports/list/?$', reports.list_, name='reports-list'),
    url(r'^reports/unclaim/(?P<report_id>\d+)/?$', reports.unclaim, name='reports-unclaim'),

    url(r'^severities/create/?$', permissions.is_staff(species.SeverityCreateView.as_view()), name='severities-create'),
    url(r'^severities/delete/(?P<pk>\d+)/?$', permissions.is_staff(species.SeverityDeleteView.as_view()), name='severities-delete'),
    url(r'^severities/detail/(?P<pk>\d+)/?$', permissions.is_staff(species.SeverityDetailView.as_view()), name='severities-detail'),
    url(r'^severities/list/?$', permissions.is_staff(species.SeverityList.as_view()), name='severities-list'),

    url(r'^species/create/?$', permissions.is_active(species.SpeciesCreateView.as_view()), name='species-create'),
    url(r'^species/delete/(?P<pk>\d+)/?$', permissions.is_active(species.SpeciesDeleteView.as_view()), name='species-delete'),
    url(r'^species/detail/(?P<pk>\d+)/?$', permissions.is_active(species.SpeciesDetailView.as_view()), name='species-detail'),
    url(r'^species/list/?$', species.list_, name='species-list'),

    url(r'^users/authenticate/?$', users.authenticate, name='users-authenticate'),
    url(r'^users/avatar/(?P<user_id>\d+)/?$', users.avatar, name='users-avatar'),
    url(r'^users/create/?$', users.create, name='users-create'),
    url(r'^users/delete/(?P<user_id>\d+)/?$', users.delete, name='users-delete'),
    url(r'^users/detail/(?P<pk>\d+)/?$', users.Detail.as_view(), name='users-detail'),
    url(r'^users/edit/(?P<user_id>\d+)/?$', users.edit, name='users-edit'),
    url(r'^users/home/?$', users.home, name='users-home'),
    url(r'^users/list/?$', users.list_, name='users-list'),
    path('users/update-name/<int:pk>/', update_user_name, name='update-user-name'),
    path('users/update-email/<int:pk>/', update_user_email, name='update-user-email'),
    path('users/update-biography/<int:pk>/', update_user_biography, name='update-user-biography'),
    path('users/update-affiliations/<int:pk>/', update_user_affiliations, name='update-user-affiliations'),

    # url(r'^login/?$', users.login, name='login'),
    url(r'^login/?$', users.LoginView.as_view(), name='login'),
    url(r'', include('django.contrib.auth.urls')),

    url(r'pages/', include('oregoninvasiveshotline.pages.urls')),
    url(r'^view-reports-page/?$', ViewReportsPageView.as_view(), name='view-reports-page'),
]


if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static('htmlcov', document_root='htmlcov', show_indexes=True)


urlpatterns += [url(r'', include('django.contrib.flatpages.urls'))]
