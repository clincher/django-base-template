# -*- coding: utf-8 -*-
from django.template import Library, TemplateSyntaxError
from django.template.defaultfilters import stringfilter
from django.utils.html import strip_tags

register = Library()

@register.filter
@stringfilter
def highlight(value, arg):
    for sequence in strip_tags(value).split(u'.'):
        if arg in sequence:
            return sequence.replace(arg, u'<dfn>{0}</dfn>'.format(arg))
    return strip_tags(value).split(u'.')[0]
highlight.is_safe = True
