# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, DetailView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

from forms import EmailAuthenticateForm
from apps.users.views import UserCreateView, UserUpdateView


urlpatterns = patterns(
    '',
    url(
        r'^password-reset/$',
        'django.contrib.auth.views.password_reset',
        name='password_reset'
    ),
    url(
        r'^login/$',
        'django.contrib.auth.views.login',
        {'authentication_form': EmailAuthenticateForm},
        name='login'
    ),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^register/$', UserCreateView.as_view(), name='register'),
    url(r'^edit/$', login_required(UserUpdateView.as_view()), name='user-edit'),
    url(r'^(?P<pk>\d+)/$',
        DetailView.as_view(model=get_user_model()),
        name='user-detail'),
    url(r'^register/success/',
        TemplateView.as_view(
            template_name='registration/register_success.html'),
        name='register-success'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^edit/', UserUpdateView.as_view(), name='user_update'),

)
