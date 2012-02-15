import tweepy
from tweepy.oauth import OAuthToken
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _


class Profile(models.Model):
    user = models.ForeignKey(User, name=_('user'), related_name='twitter_user',
            unique=True)
    screen_name = models.CharField(_('screen name'), blank=True,
            max_length=255)
    access_token = models.CharField(_('access token'), max_length=255,
            blank=True, null=True, editable=False)
    profile_image_url = models.URLField(_('profile image url'), blank=True,
            null=True)
    location = models.CharField(_('location'), max_length=100, blank=True,
            null=True)
    url = models.URLField(_('URL'), blank=True, null=True)
    description = models.CharField(_('description'), max_length=160,
            blank=True, null=True)

    class Meta:
        verbose_name = _('twitter profile')
        verbose_name_plural = _('twitter profiles')

    def __unicode__(self):
        return "%s's twitter profile" % self.user

    def get_api(self, access_token=None):
        if access_token is None:
            auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                    settings.TWITTER_CONSUMER_SECRET)
            access_token = OAuthToken.from_string(self.access_token)
        auth.access_token(access_token.key, access_token.secret)
        return tweepy.API(auth_handler=auth)
