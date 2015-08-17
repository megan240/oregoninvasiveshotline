from django.conf import settings
from django.conf.urls import include, patterns, url
from django.conf.urls.static import static
from django.contrib import admin

from .comments import views as comments
from .notifications import views as notifications
from .reports import views as reports
from .users import views as users
from .views import home

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'hotline.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # the django admin interface is always nice to have
    url(r'^admin/', include(admin.site.urls)),

    # the homepage goes straight to a template. But you may want to change this
    # into a normal view function
    url(r'^$', home, name="home"),
    url(r'^reports/create/?$', reports.create, name='reports-create'),
    url(r'^reports/detail/(?P<report_id>\d+)?$', reports.detail, name='reports-detail'),
    url(r'^reports/claim/(?P<report_id>\d+)?$', reports.claim, name='reports-claim'),
    url(r'^reports/unclaim/(?P<report_id>\d+)?$', reports.unclaim, name='reports-unclaim'),
    url(r'^reports/list/?$', reports.list_, name='reports-list'),

    url(r'^comments/edit/(?P<comment_id>\d+)?$', comments.edit, name='comments-edit'),

    url(r'^notifications/create/?$', notifications.create, name='notifications-create'),

    # Here we define all the URL routes for the users app. Technically, you
    # could put these routes in the app itself, but for non-reusable apps, we
    # keep them in the main urlconfs file
    url(r'^users/home/?$', users.home, name='users-home'),
    url(r'^users/detail/(?P<user_id>\d+)?$', users.detail, name='users-detail'),
    url(r'^users/list/?$', users.list_, name='users-list'),
    url(r'^users/create/?$', users.create, name='users-create'),
    url(r'^users/edit/(?P<user_id>\d+)/?$', users.edit, name='users-edit'),
    url(r'^users/delete/(?P<user_id>\d+)/?$', users.delete, name='users-delete'),
    url(r'^users/authenticate/?$', users.authenticate, name='users-authenticate'),
    url(r'^users/avatar/(?P<user_id>\d+)/?$', users.avatar, name='users-avatar'),

    # these url routes are useful for password reset functionality and logging in and out
    # https://github.com/django/django/blob/master/django/contrib/auth/urls.py
    url(r'^login/$', users.login, name='login'),
    url(r'', include('django.contrib.auth.urls')),

    url(r'pages/', include('hotline.pages.urls')),

    # these routes allow you to masquerade as a user, and login as them from the command line
    url(r'^cloak/', include('cloak.urls'))
)

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("htmlcov", document_root="htmlcov", show_indexes=True)

urlpatterns += (url(r'', include('django.contrib.flatpages.urls')),)
