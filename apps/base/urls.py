"""urlconf for the base application"""

from django.conf.urls import url, patterns

from .views import home


urlpatterns = patterns('',
    url(r'^$', home, name='home'),
)
