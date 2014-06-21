import datetime

from django.utils.html import avoid_wrapping
from django.utils.timezone import is_aware, utc
from django.utils.translation import ugettext


def get_rus_name_for_number(value, bits):
    if str(value).endswith('1'):
        return bits[0]
    elif str(value)[-1:] in '234':
        return bits[1]
    else:
        return bits[2]


def rutimesince(d, now=None, reversed=False):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from
    http://web.archive.org/web/20060617175230/http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
        (60 * 60 * 24 * 365, ('%d год', '%d года', '%d лет')),
        (60 * 60 * 24 * 30, ('%d месяц', '%d месяц', '%d месяцев')),
        (60 * 60 * 24 * 7, ('%d неделя', '%d недели', '%d недель')),
        (60 * 60 * 24, ('%d день', '%d дня', '%d дней')),
        (60 * 60, ('%d час', '%d часа', '%d часов')),
        (60, ('%d минута', '%d минуты', '%d минут'))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        now = datetime.datetime.now(utc if is_aware(d) else None)

    delta = (d - now) if reversed else (now - d)
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return avoid_wrapping(ugettext('0 minutes'))
    for i, (seconds, names) in enumerate(chunks):
        count = since // seconds
        name = get_rus_name_for_number(count, names)
        if count != 0:
            break
    result = avoid_wrapping(name % count)
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, names2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        name2 = get_rus_name_for_number(count2, names2)
        if count2 != 0:
            result += avoid_wrapping(', ') + avoid_wrapping(name2 % count2)
    return result
