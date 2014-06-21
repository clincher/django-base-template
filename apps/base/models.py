""" Basic models, such as user profile """
from django_comments_xtd.models import XtdComment, XtdCommentManager

from apps.ratings.fields import RatingField


class RatedComment(XtdComment):
    RATING_CHOICES = (
        (-1, 'unlike'),
        (1, 'like'),
    )

    rating = RatingField(
        range=(-1, 1), choices=RATING_CHOICES, can_change_vote=True,
        allow_anonymous=True, use_cookies=True)

    objects = XtdCommentManager()

    def __str__(self):
        return '{0}'.format(self.pk)
