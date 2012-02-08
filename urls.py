from django.conf.urls.defaults import *
from django.conf import settings
import views as topviews

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', topviews.top, name="gp-top"),
    url(r'^searchform/$', topviews.show_search_form, name="gp-search-form"),
    url(r'^search/$', topviews.search, name="gp-search-noarg"),
    url(r'^search/(?P<query>[^/]*)/$', topviews.search, name="gp-search"),
    url(r'^members/$', "recipebook.recipes.views.users.show_active_users",
        name="active-users"),
    
    url(r"", include("recipebook.recipes.urls")),
    
    url(r'^news/', include('recipebook.maricilib.django.apps.sitenews.urls')),
    url(r'^doc/', include('recipebook.maricilib.django.apps.documents.urls')),
    url(r'^feedback/', include('recipebook.maricilib.django.apps.feedback.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': settings.MEDIA_ROOT}),
    )
