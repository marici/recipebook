from django.conf.urls.defaults import patterns, url
import maintenancesettings as settings
import views as topviews
import urls


urlpatterns = patterns('django.views.generic.simple',
   url(r'maintenance', 'direct_to_template',
       {'template': 'maintenance.html',
       'extra_context': {'begin': settings.MAINTENANCE_BEGIN,
                        'end': settings.MAINTENANCE_END}},
       'top-maintenance'),
   url(r'.*', topviews.redirect_temporarily, {'url': '/maintenance'}),
)

if settings.DEBUG:
    urlpatterns = patterns('',
        url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    ) + urlpatterns

urlpatterns += urls.urlpatterns
