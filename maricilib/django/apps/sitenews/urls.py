from django.conf.urls.defaults import *

urlpatterns = patterns("maricilib.django.apps.sitenews.views",
    url(r"list/$", "show_all", name="sitenews-showlist"),
    url(r"list/(?P<page>\d+)$", "show", name="sitenews-showlist-with-page"),
    url(r"(?P<news_id>\d+)$", "show", name="sitenews-show"),
)
