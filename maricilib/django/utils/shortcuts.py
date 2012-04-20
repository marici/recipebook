# coding: utf-8
from maricilib.warnings import module_deprecated
module_deprecated(__name__, "maricilib.django.shortcuts")

from django.template import loader
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

def render_to_response_of_class(response_cls, *args, **kwargs):
    httpresponse_kwargs = {"mimetype": kwargs.pop("mimetype", None)}
    return response_cls(loader.render_to_string(*args, **kwargs), 
                        **httpresponse_kwargs)

def _get_queryset(klass):
    if isinstance(klass, QuerySet):
        return klass
    elif isinstance(klass, Manager):
        manager = klass
    else:
        manager = klass._default_manager
    return manager.all()

def get_object(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None
