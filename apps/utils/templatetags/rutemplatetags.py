from django import template
from django.template import TemplateSyntaxError
from django.template.defaultfilters import stringfilter

from apps.utils.ru_utils import rutimesince, get_rus_name_for_number

register = template.Library()


@register.filter("rutimesince", is_safe=False)
def rutimesince_filter(value, arg=None):
    """Formats a date as the time since that date (i.e. "4 days, 6 hours")."""
    if not value:
        return ''
    try:
        if arg:
            return rutimesince(value, arg)
        return rutimesince(value)
    except (ValueError, TypeError):
        return ''


@register.filter("rupluralize", is_safe=False)
@stringfilter
def rupluralize(value, arg):
    bits = arg.split(u',')
    try:
        return get_rus_name_for_number(value, bits)
    except:
        raise TemplateSyntaxError
