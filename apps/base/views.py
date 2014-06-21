""" Views for the base application """
from django.views.generic import TemplateView
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView
from django.views.generic.detail import SingleObjectMixin


class HomeView(TemplateView):
    template_name = 'homepage.html'


class ExternalRedirectView(RedirectView, SingleObjectMixin):
    def get_queryset(self):
        content_type = get_object_or_404(
            ContentType, pk=self.kwargs['content_type'])
        return content_type.model_class().objects.all()

    def get_redirect_url(self, *args, **kwargs):
        try:
            return getattr(self.get_object(), kwargs['field_name'])
        except (KeyError, AttributeError):
            raise Http404
