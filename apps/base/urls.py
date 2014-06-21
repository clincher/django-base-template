"""urlconf for the base application"""

from django.conf.urls import url, patterns
from django_comments_xtd import get_model
from apps.ratings.views import ModelRatingView

from .views import HomeView, ExternalRedirectView


urlpatterns = patterns(
    '',
    url(r'^$', HomeView.as_view(), name='home'),
    url('comment-vote/(?P<pk>\d+)/(?P<score>-?[\d]+)/',
        ModelRatingView.as_view(model=get_model()),
        name='comment-rating'
        ),
    url(r'^eredir/(?P<content_type>\d+)/(?P<pk>\d+)/(?P<field_name>[a-z_]+)/$',
        ExternalRedirectView.as_view(),
        name='redirect-view'),
)
