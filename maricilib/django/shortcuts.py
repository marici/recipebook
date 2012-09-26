# coding: utf-8
"""
The MIT License

Copyright (c) 2009 Marici, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import os
from django.template import loader
from django.template.base import TemplateDoesNotExist
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

def render_to_response_of_class(response_cls, *args, **kwargs):
    httpresponse_kwargs = {"mimetype": kwargs.pop("mimetype", None)}
    return response_cls(loader.render_to_string(*args, **kwargs),
                        **httpresponse_kwargs)


def render_to_response_device(request, template_name, *args, **kwargs):

    def find_template(template_name, suffix):
        root, ext = os.path.splitext(template_name)
        _template_name = '%s-%s%s' % (root, suffix, ext)
        try:
            loader.get_template(_template_name)
        except TemplateDoesNotExist:
            pass
        else:
            template_name = _template_name
        return template_name

    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and 'iPhone' in user_agent:
        template_name = find_template(template_name, 'iphone')
    from django.shortcuts import render_to_response
    return render_to_response(template_name, *args, **kwargs)


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
