from django.http import (
    HttpResponse, HttpResponseForbidden, HttpResponseBadRequest,
    HttpResponseNotAllowed, HttpResponseNotModified)
from django.views.generic.edit import BaseUpdateView

from .default_settings import COOKIES_MAX_AGE
from .response import HttpCreated
from .exceptions import *


class ModelRatingView(BaseUpdateView):
    """
    usage example:
    url('model-vote(?P<pk>\d+)/(?P<score>[-\d]+)/',
         RatingView.as_view(model=Model, field_name='rating)
         name='model-vote')
    """

    field_name = 'rating'
    model = None
    object = None

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(permitted_methods=['post'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            field = getattr(self.object, self.field_name)
        except AttributeError:
            return HttpResponseForbidden('Invalid field name.')

        had_voted = bool(field.get_rating_for_user(
            request.user, request.META['REMOTE_ADDR'], request.COOKIES))

        try:
            adds = field.add(kwargs['score'], request.user,
                             request.META.get('REMOTE_ADDR'), request.COOKIES)
        except IPLimitReached:
            return HttpResponseBadRequest(
                'Too many votes from this IP address for this object.')
        except AuthRequired:
            return HttpResponseForbidden('You must be logged in to vote.')
        except InvalidRating:
            return HttpResponseForbidden('Invalid rating value.')
        except CannotChangeVote:
            return HttpResponseForbidden('You have already voted.')
        except CannotDeleteVote:
            return HttpResponseForbidden('You can\'t delete this vote.')
        except NotChanged:
            return HttpResponseNotModified()
        if had_voted:
            response = HttpResponse('Vote changed.')
        else:
            response = HttpCreated('Vote recorded.')
        if 'cookie' in adds:
            cookie_name, cookie = adds['cookie_name'], adds['cookie']
            if 'deleted' in adds:
                response.delete_cookie(cookie_name)
            else:
                response.set_cookie(
                    cookie_name, cookie, COOKIES_MAX_AGE, path='/')
        return response
