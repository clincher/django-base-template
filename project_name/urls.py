""" Default urlconf for {{ project_name }} """

from django.conf.urls import include, patterns, url
from django.contrib import admin
from django.conf import settings


admin.autodiscover()


def bad(request):
    """ Simulates a server error """
    1 / 0

urlpatterns = patterns('',
    # Examples:
    url(r'', include('apps.base.urls')),
    # url(r'^comments/', include('django_comments_xtd.urls')),
    (r'^ckeditor/', include('ckeditor.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^bad/$', bad),
    # url(r'^', include('cms.urls')),
)

if settings.DEBUG:

    urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ) + urlpatterns
