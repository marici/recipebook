# -*- coding: utf-8 -*-
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
from datetime import datetime
from django.conf import settings
from django.core import urlresolvers, serializers
from django.http import (HttpResponse, Http404, HttpResponseRedirect,
                         HttpResponseForbidden,)
from django.template import loader, Context, RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from recipebook.maricilib.django.decorators import getmethod, postmethod
from recipebook.maricilib.django.shortcuts import render_to_response_of_class
from recipebook.maricilib.django.core.paginator import Paginator
from recipebook.maricilib.django.apps.taskqueue.queue import get_taskqueue
from recipebook.maricilib.django.apps.taskqueue.tasks import SendEmailTask
from recipebook.recipes.models import Contest, Recipe

per_page = 10


def show_current_contest_list(request, page=1):
    '''
    募集中のお題を表示します。募集中とは、以下のものを指します。
     * contest.publised_atが現在時刻より大きい
     * contest.closed_atが現在時刻より小さい

    @param page: ページ (デフォルトは1)
    @context page_obj: object_listにクエリセットを含むPageオブジェクト
    @return: 200レスポンス (成功)
    '''
    contests = Contest.objects.get_current_contests()
    page_obj = Paginator(contests, per_page).page(page)
    d = {'current': True,
         'title': u'レシピを募集中のお題',
         'page_obj': page_obj}
    return render_to_response('recipes/contests.html',
            d, RequestContext(request))


def show_closed_contest_list(request, page=1):
    '''
    募集が終了したお題を表示します。募集が終了したとは、以下のものを指します。
     * contest.publised_atが現在時刻より小さい
     * contest.closed_atが現在時刻より小さい

    @param page: ページ (デフォルトは1)
    @context page_obj: object_listにクエリセットを含むPageオブジェクト
    @return: 200レスポンス (成功)
    '''
    contests = Contest.objects.get_closed_contests_qs()
    page_obj = Paginator(contests, per_page).page(page)
    d = {'current': False,
         'title': u'募集終了したお題',
         'page_obj': page_obj}
    return render_to_response('recipes/contests.html',
            d, RequestContext(request))


def show_contest(request, contest_id=None):
    '''
    お題の詳細を表示します。
    is_publishedが現在時刻より小さいお題は表示できません。

    @param page: ページ (デフォルトは1)
    @context contest: Contestインスタンス
    @context contests: 全ての募集中のお題
    @return: 404レスポンス (お題が存在しないか、published_atが未来の場合)
    @return: 200レスポンス (成功)
    '''
    contest = get_object_or_404(Contest, pk=contest_id)
    if not contest.is_published():
        raise Http404
    contests = Contest.objects.get_current_contests()
    d = {'contest': contest,
         'contests': contests}
    if contest.is_really_finished():
        award_recipes = contest.get_awarded_recipes()
        d['top_award_recipes'] = award_recipes[:2]
        d['award_recipes'] = award_recipes[2:]
    return render_to_response('recipes/contest.html',
            d, RequestContext(request))


def show_recipes(request, contest_id=None, page=1):
    '''
    お題に対するレシピの一覧を新しい順に表示します。
    対象になるのは以下のレシピです。
     * recipe.contest が指定されたお題
     * is_draftがFalse

    @param contest_id: お題ID
    @param page: ページ (デフォルトは1)
    @context page_obj: object_listにRecipeインスタンスを持つPageオブジェクト
    @return: 400レスポンス (お題が存在しないか、TODO: published_atが未来の場合)
    @return: 200レスポンス (成功)
    '''
    contest = get_object_or_404(Contest, pk=contest_id)
    recipes = contest.recipe_set.filter(is_draft=False)
    page_obj = Paginator(recipes, per_page).page(page)
    links = [{'url': urlresolvers.reverse('recipes-contests-show',
                            kwargs={'contest_id': contest.id}),
              'name': contest.name}]
    d = {'title': u'%s に投稿されたレシピ一覧' % contest.name,
         'page_obj': page_obj, 'links': links}
    return render_to_response('recipes/recipes.html',
            d, RequestContext(request))


@postmethod
@login_required
def submit_recipe(request, contest_id=None, recipe_id=None):
    '''
    指定されたIDのお題に指定されたIDのレシピを投稿します。
    投稿されたレシピは、recipe.contest = contestとなります。

    レシピの作成者でなければ投稿を行うことはできません。
    また、既にお題にひもづいているレシピを再投稿することはできません。

    @param contest_id: ContestインスタンスのID
    @param recipe_id: RecipeインスタンスのID
    @return: 200レスポンス (成功。JSONを返す)
    @return: 302レスポンス (ログインしていない場合。ログインページへ)
    @return: 403レスポンス (recipe.context != None or
                         request.user != recipe.user の場合)
    @return: 404レスポンス (指定されたIDのRecipe, Contestインスタンスが存在しない場合)
    '''
    contest = get_object_or_404(Contest, pk=contest_id)
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user != request.user or recipe.contest:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    recipe.contest = contest
    recipe.save()
    data = serializers.serialize('json', [recipe])
    return HttpResponse(data, mimetype='application/javascript')


def search_contests(request, query=None, page=1):
    '''
    お題を検索します。

    @param query: 検索文字列
    @param page: 表示ページ デフォルトは1
    @context page_obj: object_listに結果を含むオブジェクト
    @return: 200レスポンス (成功)
    '''
    query = query or request.GET['query']
    title = u'%s のコンテスト検索結果' % query
    queries = query.split()
    contests = Contest.objects.search(queries, page=page, per_page=per_page)
    page_obj = Paginator(contests.get('object_list'), per_page).page(page)
    links = [{'name': u'全体から検索',
              'url': urlresolvers.reverse('gp-search',
                  kwargs={'query': query})}]
    return render_to_response('recipes/contests.html',
            {'page_obj': page_obj,
             'title': title,
             'links': links},
            RequestContext(request))


@postmethod
@login_required
def mail_recipe_template(request, contest_id=None):
    '''
    レシピテンプレートをPOSTのalter_emailで指定されたアドレスにメールで送信します。
    ログインユーザだけが行うことができます。
    alter_emailの値がprofile.alter_emailと異なる場合はprofile.alter_emailを変更します。

    @param contest_id: お題ID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのお題が存在しない場合)
    @return: 200レスポンス (レシピのJSONデータを返す。成功した場合)
    '''
    site = Site.objects.get_current()
    profile = request.user.get_profile()
    contest = get_object_or_404(Contest, pk=contest_id) if contest_id else None
    email = request.POST.get('alter_email', profile.alter_email)
    if email != profile.alter_email:
        profile.alter_email = email
    if profile.has_available_token():
        profile.token_issued_at = datetime.now()
    else:
        profile.issue_recipe_token()
    profile.save()
    c = Context({'user': request.user, 'contest': contest,
                 'token': profile.recipe_token})
    t = loader.get_template('recipes/email/recipe_template.txt')
    if contest:
        subject = u'[%s] %s へのレシピ投稿' % (site.name, contest.name)
    else:
        subject = u'[%s] レシピ投稿' % site.name
    body = t.render(c)
    task = SendEmailTask(dict(subject=subject, body=body,
                              from_address=settings.EMAIL_FROM,
                              to_list=[email]))
    get_taskqueue().send_task(task, queue_name=settings.QUEUENAME_EMAIL)
    json = serializers.serialize('json', [])
    return HttpResponse(json, mimetype='application/json')
