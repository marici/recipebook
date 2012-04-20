# coding: utf-8
'''
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
'''

import random
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from recipes.models import Contest, Recipe


def top(request):
    featured_contest = cache.get('views_top_featured_contest')
    if featured_contest is None:
        current_contests = Contest.objects.get_current_contests()
        if current_contests:
            featured_contest = random.choice(list(current_contests))
        else:
            featured_contest = None
        cache.set('views_top_featured_contest', featured_contest)
    closed_contests = Contest.objects.get_closed_contests_qs()

    d = {'featured_contest': featured_contest,
         'closed_contests': closed_contests}
    return render_to_response('top.html',
            d, RequestContext(request))


def search(request, query=None):
    query = query or request.GET['query']
    title = u'%s の検索結果' % query
    if query:
        queries = query.split()
        recipes = Recipe.objects.search(queries)
        contests = Contest.objects.search(queries, per_page=5)
    else:
        recipes = contests = []
    return render_to_response('search.html',
            {'query': query,
             'recipes': recipes,
             'contests': contests,
             'title': title},
            RequestContext(request))


def show_search_form(request):
    d = {}
    return render_to_response('search_form.html',
            d, RequestContext(request))


def redirect_temporarily(request, url):
    return HttpResponseRedirect(url)
