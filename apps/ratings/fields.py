from django.db.models import IntegerField, PositiveIntegerField, Sum, Count
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.fields import ChoiceField

from datetime import datetime

from .exceptions import *

if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImportError("ratings requires django.contrib.contenttypes "
                      "in your INSTALLED_APPS")

from django.contrib.contenttypes.models import ContentType

__all__ = ('Rating', 'RatingField', 'AnonymousRatingField')

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5

try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.now


def md5_hexdigest(value):
    return md5(value).hexdigest()


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
        self.use_cookies = self.field.allow_anonymous and self.field.use_cookies
        if self.use_cookies:
            cookie_format = 'vote-{content_type.pk}.{object_id}.{key:<6}'
            self.cookie_name = cookie_format.format(**self.default_kwargs)

    def get_ratings(self):
        """get_ratings()

        Returns a Vote QuerySet for this rating field."""
        from .models import Vote

        return Vote.objects.filter(**self.default_kwargs)
        
    def get_rating(self):
        """get_rating()
        
        Returns the average rating."""
        if not (self.votes and self.score):
            return 0
        return float(self.score) / self.votes

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
        try:
            score = int(score)
        except (ValueError, TypeError):
            raise InvalidRating("%s is not a valid choice for %s"
                                "" % (score, self.field.name))

        delete = (score == 0)
        if delete and not self.field.allow_delete:
            raise CannotDeleteVote("you are not allowed to delete votes for %s"
                                   "" % (self.field.name,))
            # ... you're also can't delete your vote if you haven't permissions
            # to change it. I leave this case for CannotChangeVote
        elif score not in self.field.range and not delete:
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
        else:
            has_changed = True
            self.votes += 1

        if has_changed:
            if not delete:
                self.score += rating.score
            if commit:
                self.instance.save()

            defaults = dict(
                score=self.score,
                votes=self.votes,
            )
            
            kwargs = self.default_kwargs.copy()

            from .models import Score

            if not Score.objects.filter(**kwargs).update(**defaults):
                kwargs.update(defaults)
                Score.objects.create(**kwargs)

        # return value
        result = {}
        if self.use_cookies:
            result['cookie_name'] = self.cookie_name
            result['cookie'] = cookie
        if delete:
            result['deleted'] = True
        return result

    def delete(self, user, ip_address, cookies=None, commit=True):
        return self.add(0, user, ip_address, cookies, commit)

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

    # def get_content_type(self):
    #     if self.content_type is None:
    #         self.content_type = ContentType.objects.get_for_model(self.instance)
    #     return self.content_type
    
    def _update(self, commit=False):
        """Forces an update of this rating
        (useful for when Vote objects are removed).
        """
        from .models import Vote, Score

        kwargs = self.default_kwargs.copy()
        votes = Vote.objects.filter(**kwargs).aggregate(
            Sum('score'), Count('score'))
        self.score = votes['score__sum']
        self.votes = votes['score__count']

        defaults = dict(
            score=self.score,
            votes=self.votes,
        )

        if not Score.objects.filter(**kwargs).update(**defaults):
            kwargs.update(defaults)
            Score.objects.create(**kwargs)

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


class RatingField(IntegerField):
    """
    A rating field contributes two columns to the model instead of the standard
     single column.
    """
    def __init__(self, *args, **kwargs):
        if kwargs.get('choices'):
            self.range = [k for k, v in kwargs['choices']]
        elif kwargs.get('range'):
            self.range = kwargs.pop('range', range(1, 2))
            kwargs['choices'] = [(i, i) for i in self.range]
        else:
            raise ImproperlyConfigured(
                "{0} imporoperly configured: attribute 'choices' or 'range' "
                "needed".format(self.__class__.__name__,))
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
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name, virtual_only=False):
        self.name = name

        # Votes tally field
        self.votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (self.name,), self.votes_field)

        # Score sum field
        self.score_field = IntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (self.name,), self.score_field)

        cls._meta.add_virtual_field(self)

        self.key = md5_hexdigest(self.name)

        field = RatingCreator(self)
        setattr(cls, name, field)

    # def get_db_prep_save(self, value, connection):
    #     pass
    #
    # def get_db_prep_lookup(self, lookup_type, value):
    #     # TODO: hack in support for __score and __votes
    #     # TODO: order_by on this field should use the weighted algorithm
    #     raise NotImplementedError(self.get_db_prep_lookup)
    #     # if lookup_type in ('score', 'votes'):
    #     #     lookup_type =
    #     #     return self.score_field.get_db_prep_lookup()
    #     if lookup_type == 'exact':
    #         return [self.get_db_prep_save(value)]
    #     elif lookup_type == 'in':
    #         return [self.get_db_prep_save(v) for v in value]
    #     else:
    #         return super(RatingField, self).get_db_prep_lookup(
    #             lookup_type, value)

    def formfield(self, **kwargs):
        defaults = {'form_class': ChoiceField}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)

    # TODO: flatten_data method


class AnonymousRatingField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousRatingField, self).__init__(*args, **kwargs)
