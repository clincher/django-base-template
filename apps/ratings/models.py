from datetime import datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# support for custom User models in Django 1.5+
try:
    from django.contrib.auth import get_user_model
except ImportError:  # django < 1.5
    from django.contrib.auth.models import User
else:
    User = get_user_model()

try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.now

from .managers import VoteManager


class Vote(models.Model):
    content_type = models.ForeignKey(ContentType, related_name="votes")
    object_id = models.PositiveIntegerField()
    key = models.CharField(max_length=32)
    score = models.FloatField()
    user = models.ForeignKey(User, blank=True, null=True, related_name="votes")
    ip_address = models.IPAddressField()
    cookie = models.CharField(max_length=32, blank=True, null=True)
    date_added = models.DateTimeField(default=now, editable=False)
    date_changed = models.DateTimeField(default=now, editable=False)

    objects = VoteManager()

    content_object = generic.GenericForeignKey()

    class Meta:
        unique_together = (('content_type', 'object_id', 'key', 'user',
                            'ip_address', 'cookie'))

    def __str__(self):
        return "%s voted %s on %s" % (
            self.user_display, self.score, self.content_object)

    def save(self, *args, **kwargs):
        self.date_changed = now()
        super(Vote, self).save(*args, **kwargs)

    def user_display(self):
        if self.user:
            return "%s (%s)" % (self.user.email, self.ip_address)
        return self.ip_address
    user_display = property(user_display)

    def partial_ip_address(self):
        ip = self.ip_address.split('.')
        ip[-1] = 'xxx'
        return '.'.join(ip)
    partial_ip_address = property(partial_ip_address)
