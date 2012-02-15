import tweepy
from django.conf import settings
from django.contrib.auth.models import User
from maricilib.django.apps.twitter.models import Profile


class TwitterAuthBackend(object):

    def authenticate(self, access_token, user=None):
        auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                settings.TWITTER_CONSUMER_SECRET)
        auth.set_access_token(access_token.key, access_token.secret)
        api = tweepy.API(auth_handler=auth)

        me = api.me()
        profile = None
        if user is None:
            user, created = User.objects.get_or_create(
                    username='twitter:%s' % me.id)
            if created:
                temp_password = User.objects.make_random_password(length=12)
                user.set_password(temp_password)

        user.first_name = me.screen_name
        user.save()

        profile, created = Profile.objects.get_or_create(user=user)
        profile.screen_name = me.screen_name
        profile.access_token = access_token
        profile.url = me.url
        profile.location = me.location
        profile.description = me.description
        profile.profile_image_url = me.profile_image_url
        profile.save()

        return user

    def get_user(self, id):
        try:
            return User.objects.get(pk=id)
        except:
            return None
