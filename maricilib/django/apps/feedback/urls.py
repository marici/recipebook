from django.conf.urls.defaults import *

urlpatterns = patterns("recipebook.maricilib.django.apps.feedback.views",
    url(r"^submit$", "submit", name="feedback-submit"),
)
