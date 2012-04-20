from django.conf.urls.defaults import *

urlpatterns = patterns("maricilib.django.apps.feedback.views",
    url(r"^submit$", "submit", name="feedback-submit"),
)
