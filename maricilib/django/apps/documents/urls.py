from django.conf.urls.defaults import *

urlpatterns = patterns("recipebook.maricilib.django.apps.documents.views",
    url(r"^$", "index", name="documents-index"),
    url(r"^(?P<label>\w+)/(?P<format>.*)$", "show", 
        name="documents-show-with-format"),
    url(r"^(?P<label>\w+)$", "show", name="documents-show"),
)
