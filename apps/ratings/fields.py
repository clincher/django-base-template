from hashlib import md5

from django.contrib.contenttypes.models import ContentType
from django.db.models import FloatField, PositiveIntegerField, Sum, Count
from django.conf import settings
from django.forms.fields import ChoiceField
from django.utils.timezone import now

from .exceptions import *

__all__ = ('Rating', 'RatingField', 'AnonymousRatingField')


class Rating(object):
    def __init__(self, score, votes):
        self.score = score
        self.votes = votes


class RatingManager(object):
    def __init__(self, instance, field):
        self.instance = instance
        self.field = field
        self.default_kwargs = dict(
            content_type=ContentType.objects.get_for_model(self.instance),
            object_id=self.instance.pk,
            key=self.field.key
        )
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
        self.rating_field_name = "%s_rating" % (self.field.name,)
        self.use_cookies = self.field.allow_anonymous and self.field.use_cookies
        if self.use_cookies:
            cookie_format = 'vote-{content_type.pk}.{object_id}.{key:<6}'
            self.cookie_name = cookie_format.format(**self.default_kwargs)

    def get_ratings(self):
        """get_ratings()

        Returns a Vote QuerySet for this rating field."""
        from .models import Vote

        return Vote.objects.filter(**self.default_kwargs)

    def percent_rating(self):
        return self.rating * 100

    def get_rating_for_user(self, user, ip_address=None, cookies=None):
        """get_rating_for_user(user, ip_address=None, cookie=None)
        
        Returns the rating for a user or anonymous IP."""
        kwargs = self.default_kwargs.copy()

        if user.is_authenticated():
            kwargs['user'] = user
        else:
            if not ip_address:
                raise ValueError('``user`` or ``ip_address`` must be present.')
            kwargs['user__isnull'] = True
            kwargs['ip_address'] = ip_address

        if self.use_cookies and isinstance(cookies, dict):
            cookie = cookies.get(self.cookie_name)
            if cookie:
                kwargs['cookie'] = cookie
            else:
                kwargs['cookie__isnull'] = True
        from .models import Vote

        try:
            rating = Vote.objects.get(**kwargs)
            return rating.score
        except Vote.MultipleObjectsReturned:
            pass
        except Vote.DoesNotExist:
            pass
        return

    def add(self, score, user, ip_address, cookies=None, commit=True):
        """add(score, user, ip_address)
        
        Used to add a rating to an object."""
        delete = False
        try:
            score = float(score)
        except (ValueError, TypeError):
            if score == '.':
                delete = True
            else:
                raise InvalidRating("%s is not a valid choice for %s"
                                    "" % (score, self.field.name))

        if delete and not self.field.allow_delete:
            raise CannotDeleteVote("you are not allowed to delete votes for %s"
                                   "" % (self.field.name,))
            # ... you're also can't delete your vote if you haven't permissions
            # to change it. I leave this case for CannotChangeVote
        elif (score < self.field.range[0]
              or score > self.field.range[1]) and not delete:
            raise InvalidRating("%s is not a valid choice for %s"
                                "" % (score, self.field.name))

        if user.is_anonymous() and not self.field.allow_anonymous:
            raise AuthRequired("user must be a user, not '%r'" % (user,))
        elif user.is_anonymous():
            user = None

        defaults = dict(
            score=score,
            ip_address=ip_address,
        )

        kwargs = self.default_kwargs.copy()
        kwargs['user'] = user

        if not user:
            kwargs['ip_address'] = ip_address

        from .models import Vote

        if self.use_cookies:
            defaults['cookie'] = now().strftime('%Y%m%d%H%M%S%f')
            cookie = cookies.get(self.cookie_name)
            if cookie:
                kwargs['cookie'] = cookie
            else:
                kwargs['cookie__isnull'] = True

        try:
            rating, created = Vote.objects.get(**kwargs), False
        except Vote.DoesNotExist:
            if delete:
                raise CannotDeleteVote(
                    "attempt to find and delete your vote for %s is failed"
                    "" % (self.field.name,))
            if getattr(settings, 'RATINGS_VOTES_PER_IP', None):
                num_votes = Vote.objects.filter(
                    ip_address=ip_address, **self.default_kwargs).count()
                if num_votes >= settings.RATINGS_VOTES_PER_IP:
                    raise IPLimitReached()
            kwargs.update(defaults)
            if self.use_cookies:
                # record with specified cookie was not found ...
                # ...we need to replace old cookie (if presented) with a new
                cookie = defaults['cookie']
                # ... and remove 'cookie__isnull' from .create()'s **kwargs
                kwargs.pop('cookie__isnull')
            rating, created = Vote.objects.create(**kwargs), True

        if not created:
            if self.field.can_change_vote:
                if score == rating.score:
                    raise NotChanged()
                has_changed = True
                self.score -= rating.score
                # you can delete your vote only
                # if you have permission to change your vote
                if delete:
                    self.votes -= 1
                    rating.delete()
                else:
                    rating.score = score
                    rating.save()
            else:
                raise CannotChangeVote()
        else:  # if created
            has_changed = True
            self.votes += 1

        if has_changed:
            if not delete:
                self.score += rating.score

            difference = self.score / self.votes - self.rating.range[0]
            max_difference = self.rating.range[1] - self.rating.range[0]
            self.rating = difference / max_difference

            if commit:
                self.instance.save()

        # return value
        result = {}
        if self.use_cookies:
            result['cookie_name'] = self.cookie_name
            result['cookie'] = cookie
        if delete:
            result['deleted'] = True
        return result

    def delete(self, user, ip_address, cookies=None, commit=True):
        return self.add('.', user, ip_address, cookies, commit)

    @property
    def votes(self, default=None):
        return getattr(self.instance, self.votes_field_name, default)

    @votes.setter
    def votes(self, value):
        setattr(self.instance, self.votes_field_name, value)

    @property
    def score(self, default=None):
        return getattr(self.instance, self.score_field_name, default)

    @score.setter
    def score(self, value):
        setattr(self.instance, self.score_field_name, value)

    @property
    def rating(self, default=None):
        return getattr(self.instance, self.rating_field_name, default)

    @rating.setter
    def rating(self, value):
        setattr(self.instance, self.rating_field_name, value)

    def _update(self, commit=False):
        """Forces an update of this rating
        (useful for when Vote objects are removed).
        """
        from .models import Vote

        kwargs = self.default_kwargs.copy()
        votes = Vote.objects.filter(**kwargs).aggregate(
            Sum('score'), Count('score'))
        self.score = votes['score__sum']
        self.votes = votes['score__count']

        if commit:
            self.instance.save()


class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)

    def __get__(self, instance, cls):
        if instance is None:
            return self.field
        return RatingManager(instance, self.field)

    def __set__(self, instance, value):
        if isinstance(value, Rating):
            setattr(instance, self.votes_field_name, value.votes)
            setattr(instance, self.score_field_name, value.score)
        else:
            raise TypeError("%s value must be a Rating instance, not '%r'" % (
                self.field.name, value))


class RatingField(FloatField):
    """
    A rating field contributes two columns to the model instead of the standard
     single column.
    """
    def __init__(self, *args, **kwargs):
        self.range = kwargs.pop('range')
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        self.allow_anonymous = kwargs.pop('allow_anonymous', False)
        self.use_cookies = kwargs.pop('use_cookies', False)
        self.allow_delete = kwargs.pop('allow_delete', False)
        kwargs['editable'] = False
        kwargs['default'] = 0
        kwargs['blank'] = True
        self.key = None
        self.votes_field = None
        self.score_field = None
        self.rating_field = None
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name, virtual_only=False):
        self.name = name

        # Votes tally field
        self.votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (self.name,), self.votes_field)
        # Score sum field
        self.score_field = FloatField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (self.name,), self.score_field)
        # rating field
        self.rating_field = FloatField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_rating" % (self.name,), self.rating_field)

        cls._meta.add_virtual_field(self)
        self.key = md5(self.name.encode('utf-8')).hexdigest()
        field = RatingCreator(self)
        setattr(cls, name, field)

    def formfield(self, **kwargs):
        defaults = {'form_class': ChoiceField}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)


class AnonymousRatingField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousRatingField, self).__init__(*args, **kwargs)
