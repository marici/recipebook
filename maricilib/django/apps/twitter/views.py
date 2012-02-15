# -*- coding: utf-8 -*-
import logging
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth as auth_module
import tweepy

logger = logging.getLogger('maricilib.django.apps.twitter')


def login(request):
    callback_url = getattr(settings, 'TWITTER_CALLBACK_URL', None)
    if not callback_url:
        callback_url = '%s://%s%s' % (
                'https' if request.is_secure() else 'http',
                request.get_host(),
                reverse('twitter-oauth_callback'))
    auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET, callback_url)
    auth_url = auth.get_authorization_url()
    request.session['request_token'] = (auth.request_token.key,
            auth.request_token.secret)
    return HttpResponseRedirect(auth_url)


def oauth_callback(request):
    auth_user = None
    try:
        verifier = request.GET.get('oauth_verifier')
        auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY,
                settings.TWITTER_CONSUMER_SECRET)

        token = request.session.get('request_token')
        auth.set_request_token(token[0], token[1])
        auth.get_access_token(verifier)

        if 'request_token' in request.session:
            del request.session['request_token']
        request.session['twitter_access_token'] = auth.access_token.to_string()

        user = request.user if request.user.is_authenticated() else None
        auth_user = auth_module.authenticate(access_token=auth.access_token,
                user=user)
        if auth_user:
            auth_module.login(request, auth_user)
    except Exception, e:
        logger.warn(e)

    if auth_user is None:
        if 'access_token' in request.session:
            del request.session['access_token']
        messages.add_message(request, messages.ERROR,
                message=(u'ログインできませんでした。'
                    u'しばらくしてからもう一度お試しください。'))
        return HttpResponseRedirect(settings.TWITTER_LOGIN_FAILUE_URL)

    return HttpResponseRedirect(settings.TWITTER_LOGIN_SUCCESS_URL)
