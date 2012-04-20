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
from datetime import datetime
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from maricilib.django.core.paginator import Paginator
from maricilib.django.apps.sitenews.models import SiteNews

per_page = 20

def show(request, news_id=None):
    sitenews = get_object_or_404(SiteNews, pk=news_id)
    if not sitenews.is_open or datetime.now() < sitenews.published_at:
        raise Http404
    d = {"sitenews":sitenews}
    return render_to_response("sitenews/news.html",
        d, RequestContext(request))

def show_all(request, page=1):
    news_list = SiteNews.objects.filter(is_open=True).filter(published_at__lt=datetime.now())
    page_obj = Paginator(news_list, per_page).page(page)
    d = {"page_obj":page_obj}
    return render_to_response("sitenews/list.html",
        d, RequestContext(request))
    
