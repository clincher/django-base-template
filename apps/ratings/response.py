# -*- coding: utf-8 -*-


from django.http.response import HttpResponse


class HttpCreated(HttpResponse):
    status_code = 201
