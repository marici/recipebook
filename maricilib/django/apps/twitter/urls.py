from django.conf.urls.defaults import *

urlpatterns = patterns('recipebook.maricilib.django.apps.twitter.views',
    url(r'login/?$', 'login', name='twitter-login'),
    url(r'oauth_callback$', 'oauth_callback', name='twitter-oauth_callback'),
)
