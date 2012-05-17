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
from django.conf import settings
from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import (HttpResponse, Http404, HttpResponseRedirect,
                         HttpResponseForbidden,)
from django.template import loader, Context, RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.contrib import messages
from django.contrib.sites.models import Site
from maricilib.django.core.paginator import Paginator
from maricilib.django.shortcuts import (render_to_response_of_class,
        render_to_response_device)
from maricilib.django.decorators import getmethod, postmethod
from maricilib.django.apps.taskqueue.queue import get_taskqueue
from maricilib.django.apps.taskqueue.tasks import SendEmailTask
from recipes.models import (Recipe, Contest, User, UserProfile, Direction,
        Comment, FavoriteRecipe)
from recipes import forms


def user_is_active_or_404(user):
    if not user.is_active:
        raise Http404


def show_recipe(request, recipe_id=None, recipe_model=Recipe,
        template_name='recipes/recipe.html'):
    '''
    指定されたIDのレシピ詳細ページを出力します。
    レシピがis_draft == Trueの場合、作成したユーザのみ見ることができます。

    @param recipe_id: RecipeインスタンスのID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @param template_name: レンダするテンプレートパス
    @context recipe: Recipeインスタンス
                     (recipe.id == recipe_id)
    @return: 403レスポンス (recipe.is_draft == True and
                         request.user != recipe.user の場合)
    @return: 404レスポンス (指定されたIDのRecipeインスタンスが存在しない場合)
    @return: 404レスポンス (指定レシピの作成ユーザがis_active=Falseの場合)
    @return: 200レスポンス (成功。詳細ページを表示)
    '''
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    recipe_user = recipe.user
    if not recipe.is_awarded:
        user_is_active_or_404(recipe_user)
    if recipe.is_draft and request.user != recipe_user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    recipe.set_request_user(request.user)
    comment_form = None
    profile = recipe_user.get_profile()
    if not profile.deny_comment:
        comment_form = forms.CommentForm()
    submit_form = forms.SubmitToContestForm()
    d = {'recipe': recipe, 'comment_form': comment_form,
         'submit_form': submit_form}
    return render_to_response_device(request, template_name,
            d, RequestContext(request))


@getmethod
def show_recipe_for_print(request, recipe_id=None, recipe_model=Recipe,
        template_name='recipes/recipe_print.html'):
    '''
    指定されたIDのレシピ詳細ページ(印刷向け)を出力します。
    条件はshow_recipeと同じです。
    '''
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    if not recipe.is_awarded:
        user_is_active_or_404(recipe.user)
    if recipe.is_draft and request.user != recipe.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    recipe.set_request_user(request.user)
    d = {'recipe': recipe}
    return render_to_response(template_name, d, RequestContext(request))


@getmethod
@login_required
def register_recipe(request, contest_id=None, contest_model=Contest,
        recipe_form=forms.NewRecipeForm,
        template_name='recipes/new_recipe_form.html',
        redirect_to=None):
    '''
    レシピの新規作成フォームページを出力します。
    コンテキストに含まれるformはContestモデルのrecipe_formメソッドが返す値です。

    @param contest_id: お題ID（なくても可）
    @param contest_model: Contestクラスまたはサブクラス (デフォルト: Contest)
    @param recipe_form: 出力するFormクラス (デフォルト: NewRecipeForm)
    @param template_name: レンダするテンプレートパス
    @context form: 指定したFormのインスタンス
    @return: 302レスポンス (ログインしていない場合)
    @return: 200レスポンス (成功。フォームを表示)
    '''
    form = recipe_form()
    d = {'form': form}
    return render_to_response(template_name, d, RequestContext(request))


@postmethod
@login_required
def register_recipe(request, contest_id=None, contest_model=Contest,
        recipe_form=forms.NewRecipeForm,
        template_name='recipes/new_recipe_form.html',
        redirect_to=lambda recipe: reverse('recipes-edit',
            kwargs={'recipe_id': recipe.id})):
    '''
    レシピデータを新規作成します。
    form_classで定義された値を受け取ります。
    必須項目はform_classにより決定されます。
    レシピの作成が成功した場合、編集ページにリダイレクトされます。

    Contextで返されるRecipeインスタンスは以下の状態になっています。
    name, introduction, feeling, photo: フォームから渡された値
    user: ログインユーザ
    is_draft: True
    contest: 指定されたお題のID

    @param contest_id: お題ID (optional)
    @param contest_model: Contestクラスまたはサブクラス (デフォルト: Contest)
    @context recipe_form: recipe_formインスタンス (フォームがinvalidの場合)
    @param template_name: レンダするテンプレートパス
    @param redirect_to: recipeインスタンスを受け取りリダイレクトパスを返すcallable
    @return: 403レスポンス (TODO: 指定のお題が存在しない場合)
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 302レスポンス (レシピ編集ページへ。作成に成功した場合)
    '''
    form = recipe_form(request.POST, request.FILES)
    if not form.is_valid():
        return render_to_response(template_name, {'form': form},
                RequestContext(request))
    recipe = form.save(commit=False)
    recipe.user = request.user
    if contest_id:
        contest = contest_model.objects.get(pk=contest_id)
        try:
            contest.pre_submit_recipe(request.user, recipe)
        except Contest.NotAllowedSubmit:
            pass  # ignored by contest
        else:
            recipe.contest = contest
    recipe.save()
    redirect_path = redirect_to(recipe)
    return HttpResponseRedirect(redirect_path)


@postmethod
@login_required
def toggle_recipe_open_state(request, recipe_id=None):
    '''
    指定されたIDのレシピの公開状態を変更します。
    レシピが下書き状態(is_draft==True)の場合、公開状態(is_draft==False)に変更します。
    公開状態の場合、下書き状態に変更します。
    レシピを作成したユーザだけが状態の変更を行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合
                          商品化が決定している場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (JSONが返される。成功した場合)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if request.user != recipe.user or recipe.is_awarded:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    recipe.toggle_open_state()
    recipe.save()
    data = serializers.serialize('json', [recipe])  # TODO: 情報を削減
    return HttpResponse(data, mimetype='application/json')


def render_edit_recipe_page(request, recipe, form):
    '''
    レシピの編集画面を出力します。(この関数はビュー関数ではありません。)
    '''
    directions = recipe.ordered_directions()
    d_form = forms.DirectionForm()
    d = {'form': form,
         'direction_form': d_form,
         'recipe': recipe,
         'directions': directions}
    return render_to_response('recipes/edit_recipe_form.html',
            d, RequestContext(request))


@getmethod
@login_required
def edit_recipe(request, recipe_id=None, recipe_model=Recipe,
        recipe_form=forms.RecipeForm):
    '''
    指定されたIDのレシピの編集画面を表示します。
    レシピを作成したユーザだけが表示を行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @param recipr_form: 出力するフォーム (デフォルト: RecipeForm)
    @context recipe: Recipeインスタンス
    @context directions: クエリセット。recipe.direction_set.all()
    @context form: RecipeFormインスタンス
    @context direction_form: DirectionFormインスタンス
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合
                         一度でも公開したことがあり、既にお題にひもづいている場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (成功。フォームを表示)
    '''
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    if (request.user != recipe.user or \
        recipe.is_awarded or \
        (recipe.contest and recipe.published_at)):
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    form = forms.RecipeForm(instance=recipe)
    return render_edit_recipe_page(request, recipe, form)


@postmethod
@login_required
def edit_recipe(request, recipe_id=None, recipe_model=Recipe,
        recipe_form=forms.RecipeForm):
    '''
    指定されたIDのレシピデータの変更を行います。
    レシピを作成したユーザだけが変更を行うことができます。(recipe.user==request.user)
    forms.RecipeFormで定義された値を受け取ります。
    また、複数の素材データ(食材: foodパラメータのリストと分量: quantityパラメータのリスト)を
    JSON文字列にエンコードします。
    素材データはrecipe.decode_ingredients()でタプル(食材名,分量)のリストに
    復元することができます。

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @param recipr_form: 出力するフォーム (デフォルト: RecipeForm)
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合
                         一度でも公開したことがあり、既にお題にひもづいている場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 302レスポンス (レシピ編集ページへ。成功した場合)
    '''
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    if (request.user != recipe.user or
        recipe.is_awarded or
        (recipe.contest and recipe.published_at)):
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    recipe.encode_ingredients(request.POST.getlist('food'),
        request.POST.getlist('quantity'))
    form = recipe_form(request.POST, request.FILES, instance=recipe)
    if form.is_valid():
        recipe = form.save()
        messages.add_message(request, messages.INFO, u'レシピを保存しました。')
    return HttpResponseRedirect(reverse('recipes-edit',
                                        kwargs={'recipe_id': recipe.id}))


@postmethod
@login_required
def delete_recipe(request, recipe_id=None, recipe_model=Recipe):
    '''
    指定されたIDのレシピを削除します。
    レシピを作成したユーザだけが行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合
                         商品化が決定している場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 302レスポンス (POSTのredirect_pathの値、
                         またはsettings.LOGIN_REDIRECT_URLへ。成功した場合)
    '''
    redirect_path = request.POST.get('redirect_path',
                                     settings.LOGIN_REDIRECT_URL)
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    if recipe.user != request.user or recipe.is_awarded:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    message = u'%s を削除しました。' % recipe.name
    recipe.delete()
    messages.add_message(request, messages.INFO, message)
    return HttpResponseRedirect(redirect_path)


@postmethod
@login_required
def mail_recipe(request, recipe_id=None, recipe_model=Recipe,
        template_name='recipes/email/mail_recipe.txt'):
    '''
    指定されたIDのレシピの情報をPOSTのalter_emailで指定されたアドレスにメールで送信します。
    ログインユーザだけが行うことができます。
    alter_emailの値がprofile.alter_emailと異なる場合はprofile.alter_emailを変更します。

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (レシピのJSONデータを返す。成功した場合)
    '''
    site = Site.objects.get_current()
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    profile = request.user.get_profile()
    email = request.POST.get('alter_email', profile.alter_email)
    if email != profile.alter_email:
        profile.alter_email = email
        profile.save()
    c = Context({'user': request.user, 'recipe': recipe})
    t = loader.get_template(template_name)
    subject = u'[%s] %s' % (site.name, recipe.name)
    body = t.render(c)
    task = SendEmailTask(dict(subject=subject, body=body,
                              from_address=settings.EMAIL_FROM,
                              to_list=[email]))
    get_taskqueue().send_task(task, queue_name=settings.QUEUENAME_EMAIL)
    json = serializers.serialize('json', [recipe])  # TODO: 情報削減
    return HttpResponse(json, mimetype='application/json')


@postmethod
@login_required
def submit_recipe_to_contest(request, recipe_id, recipe_model=Recipe,
        contest_model=Contest):
    '''
    指定されたIDのレシピをPOSTのcontestの値で指定されたお題に投稿します。
    レシピの作成ユーザだけが行うことができます。
    成功後のレシピは以下の状態になります。
    contest: 指定されたIDのContestインスタンス

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @param contest_model: Contestクラスまたはサブクラス (デフォルト: Contest)
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 403レスポンス (ログインユーザが作成者ではない場合)
    @return: 403レスポンス (TODO: 指定のお題が存在しない場合)
    @return: 200レスポンス (レシピのJSONデータを返す。成功した場合)
    '''
    recipe = get_object_or_404(recipe_model, pk=recipe_id)
    if request.user != recipe.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    contest_id = request.POST.get('contest', None)
    if contest_id:
        contest = contest_model.objects.get(pk=contest_id)
        recipe.contest = contest
        recipe.save()
        json = serializers.serialize('json', [contest])
    else:
        json = ''
    return HttpResponse(json, mimetype='application/json')


def show_voting_users(request, recipe_id):
    '''
    指定されたIDのレシピに投票したユーザの一覧を表示します。

    @param recipe_id: レシピID
    @context users_and_profiles: ユーザとプロファイルを持つリスト
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 404レスポンス (指定レシピのユーザがis_active=Falseの場合)
    @return: 200レスポンス (成功した場合)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user_is_active_or_404(recipe.user)
    user_ids = recipe.vote_set.filter(recipe=recipe).values('user_id').query
    users = User.objects.filter(pk__in=user_ids)
    u_and_p = UserProfile.objects.get_zipped_profiles(users,
                                                  users.values('pk').query)
    links = [{'name': recipe.name,
              'url': reverse('recipes-show', kwargs={'recipe_id': recipe.id})}]
    d = {'users_and_profiles': u_and_p, 'links': links,
         'title': u'%s に投票したメンバー' % recipe.name}
    return render_to_response('recipes/users.html',
                              d, RequestContext(request))


@postmethod
def copy_recipe(request, recipe_id=None, recipe_model=Recipe):
    '''
    指定されたIDのレシピをコピーして、ログインユーザのレシピを作成します。
    作成者以外の場合、下書きをコピーすることはできません。
    結果ステータスを含むJSONを返します。

    @param recipe_id: レシピID
    @param recipe_model: Recipeクラスまたはサブクラス (デフォルト: Recipe)
    @return: 403レスポンス (ログインしていない場合)
    @return: 403レスポンス (指定されたレシピが下書きであり、作成者がログインユーザではない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (成功。結果とレシピIDをJSONで出力)
    '''
    failure_json = simplejson.dumps({'status': 'failure'})
    if request.user is None or not request.user.is_active:
        return HttpResponse(failure_json, 'application/json', 403)
    try:
        recipe = recipe_model.objects.get(pk=recipe_id)
    except Recipe.DoesNotExist:
        return HttpResponse(failure_json, 'application/json', 404)
    if not recipe.user.is_active:
        return HttpResponse(failure_json, 'application/json', 404)
    if recipe.is_draft and recipe.user != request.user:
        return HttpResponse(failure_json, 'application/json', 403)
    new_recipe = recipe.copy(request.user)
    json = simplejson.dumps({'status': 'success', 'recipe_id': new_recipe.pk})
    return HttpResponse(json, 'application/json')


@postmethod
@login_required
def register_direction(request, recipe_id=None):
    '''
    指定されたIDのレシピに関する作り方データを新規作成します。
    レシピを作成したユーザだけが作成を行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (成功。DirectionインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user != request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    form = forms.DirectionForm(request.POST, request.FILES)
    if not form.is_valid():
        json = simplejson.dumps({'status': 'error',
            'message': 'form is not valid.'})
        direction = None
    else:
        direction = form.save(commit=False)
        recipe.add_direction(direction)
        direction.save()
        d = {'status': 'success',
             'message': '',
             'direction': {'pk': direction.id,
                 'fields': {'text': direction.text,
                 'photo': direction.photo and direction.photo.url or ''}}}
        json = simplejson.dumps(d)
    if direction.photo:
        data = '<textarea>%s</textarea>' % json
    else:
        data = json
    return HttpResponse(data, mimetype='text/html')


@postmethod
@login_required
def edit_direction(request, recipe_id=None, direction_id=None):
    '''
    指定されたIDの作り方データを変更します。
    レシピを作成したユーザだけが行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合)
    @return: 403レスポンス (指定の作り方が指定のレシピにひもづいていない場合)
    @return: 200レスポンス (成功。DirectionインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user != request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    direction = get_object_or_404(Direction, pk=direction_id)
    if recipe != direction.recipe:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    text = request.POST.get('text')
    direction.text = text
    direction.save()
    json = serializers.serialize('json', [direction])
    return HttpResponse(json, mimetype='application/json')


@postmethod
@login_required
def delete_direction(request, recipe_id=None, direction_id=None):
    '''
    指定されたIDの作り方データを削除します。
    レシピを作成したユーザだけが行うことができます。(recipe.user==request.user)

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合)
    @return: 403レスポンス (指定の作り方が指定のレシピにひもづいていない場合)
    @return: 200レスポンス (成功。DirectionインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user != request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    direction = get_object_or_404(Direction, pk=direction_id)
    if recipe != direction.recipe:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    json = serializers.serialize('json', [direction])
    direction.delete()
    return HttpResponse(json, mimetype='application/json')


@postmethod
@login_required
def sort_directions(request, recipe_id=None):
    '''
    指定されたIDのレシピにひもづく作り方データを並べ替えます。
    レシピを作成したユーザだけが行うことができます。(recipe.user==request.user)
    POSTのdirection[]の値リストに含まれる、作り方IDの順序通りになります。

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザではない場合)
    @return: 200レスポンス (成功。DirectionインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user != request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    direction_ids = request.POST.getlist('direction[]')
    direction_dict = {}
    for direction in recipe.direction_set.all():
        direction_dict[direction.id] = direction
    for i, direction_id in enumerate(direction_ids):
        direction = direction_dict[int(direction_id)]
        direction.number = i
        direction.save()
    json = simplejson.dumps(direction_ids)
    return HttpResponse(json, mimetype='application/json')


@postmethod
@login_required
def add_favorite_recipe(request, recipe_id=None):
    '''
    指定されたIDのレシピをログインユーザのフェイバリットに登録します。
    レシピを作成したユーザを除くユーザだけが作成を行うことができます。(recipe.user!=request.user)

    JSONで返されるFavoriteRecipeインスタンスは以下の状態になっています。
    user: ログインユーザ
    recipe: 指定されたIDのRecipeインスタンス

    @param recipe_id: レシピID
    @context favorite_recipe: 作成されたFavoriteRecipeインスタンス
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたレシピの作成者がログインユーザの場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合、または作成者がis_active=Falseの場合)
    @return: 200レスポンス (成功。FavoriteRecipeインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user_is_active_or_404(recipe.user)
    if recipe.user == request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    fav = recipe.favorite(request.user)
    data = serializers.serialize('json', [fav])
    return HttpResponse(data, mimetype='application/json')


@postmethod
@login_required
def remove_favorite_recipe(request, recipe_id=None):
    '''
    指定されたIDのレシピをログインユーザのフェイバリットから削除します。
    該当のFavoriteRecipeインスタンスを作成したユーザだけが削除を行うことができます。
    成功した場合、削除されたFavoriteRecipeインスタンスがJSONで返ります。

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (ログインユーザがレシピの作成者である場合)
    @return: 403レスポンス (ログインユーザが該当のFavoriteRecipeインスタンスを作成していない場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合)
    @return: 200レスポンス (成功。FavoriteRecipeインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    if recipe.user == request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    try:
        fav = FavoriteRecipe.objects.get(user=request.user, recipe=recipe)
        data = serializers.serialize('json', [fav])
        fav.delete()
    except:
        raise Http404
    return HttpResponse(data, mimetype='application/json')


@postmethod
@login_required
def vote_to_recipe(request, recipe_id=None):
    '''
    指定されたIDのレシピに投票します。
    レシピ作成者ではないログインユーザだけが行うことができます。

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (ログインユーザがレシピの作成者である場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合、または作成者がis_active=Falseの場合)
    @return: 200レスポンス (成功。VoteインスタンスをJSONで出力)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    user_is_active_or_404(recipe.user)
    if recipe.user == request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    vote = recipe.vote(request.user)
    recipe.save()
    data = serializers.serialize('json', [vote])
    return HttpResponse(data, mimetype='application/json')


@postmethod
@login_required
def comment_to_recipe(request, recipe_id=None):
    '''
    指定されたIDのレシピにコメントします。
    ログインユーザだけが行うことができます。
    POSTする項目はCommentFormの定義に従います。
    作成成功時、ログインユーザがレシピの作成者の場合は、is_moderatedはTrueになります。
    それ以外の場合はFalseになり、レシピ閲覧画面に表示されません。

    @param recipe_id: レシピID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定レシピの作成者がprofile.deny_comment == Trueの場合)
    @return: 404レスポンス (指定されたIDのレシピが存在しない場合、または作成者がis_active=Falseの場合)
    @return: 200レスポンス (not form.is_valid()の場合、フォームを再表示)
    @return: 302レスポンス (成功。レシピ閲覧ページにリダイレクトする)
    '''
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    recipe_user = recipe.user
    user_is_active_or_404(recipe_user)
    profile = recipe_user.get_profile()
    if profile.deny_comment:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    form = forms.CommentForm(request.POST, request.FILES)
    if not form.is_valid():
        message = u'コメント内容に問題があります。'
        messages.add_message(request, messages.INFO, message)
        d = {'recipe': recipe, 'comment_form': form,
             'submit_form': forms.SubmitToContestForm()}
        return render_to_response('recipes/recipe.html',
            d, RequestContext(request))
    comment = form.save(commit=False)
    comment.user = request.user
    comment.recipe = recipe
    comment.owner = recipe_user
    if recipe_user == request.user:
        comment.approve()
        message = u'コメントが登録されました。'
    else:
        message = u'コメントを受け付けました。%s さんが承認すると表示されます。' % recipe_user.first_name
    comment.save()
    messages.add_message(request, messages.INFO, message)
    return HttpResponseRedirect(reverse('recipes-show',
                                        kwargs={'recipe_id': recipe.id}))


@postmethod
@login_required
def delete_comment(request, comment_id):
    '''
    コメントを削除します。
    削除できるのはコメントしたユーザかコメント先のレシピを作成したユーザだけです。

    @param comment_id: コメントID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 404レスポンス (指定されたIDのコメントが存在しない場合)
    @return: 403レスポンス (ログインユーザがレシピ、コメントの作成者でない場合)
    @return: 200レスポンス (成功。コメントのJSONデータが返ります)
    '''
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user not in (comment.owner, comment.user):
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    json = serializers.serialize('json', [comment])
    if comment.is_moderated:
        recipe = comment.recipe
        recipe.delete_comment(comment)
        recipe.save()
    comment.delete()
    return HttpResponse(json, mimetype='application/json')


@postmethod
@login_required
def approve_comment(request, comment_id):
    '''
    コメントを承認します。これにより他のユーザにコメントが見えるようになります。
    承認できるのはコメント先のレシピを作成したユーザだけです。

    @param comment_id: コメントID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (ログインユーザがレシピの作成者でない場合)
    @return: 404レスポンス (指定されたIDのコメントが存在しない場合)
    @return: 200レスポンス (成功。コメントのJSONデータを返す)
    '''
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.owner:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    comment.approve()
    comment.save()
    json = serializers.serialize('json', [comment])
    return HttpResponse(json, mimetype='application/json')


def search_recipes(request, query=None, page=1):
    '''
    レシピを検索します。

    @param query: 検索文字列
    @param page: 表示ページ デフォルトは1
    @context page_obj: object_listに結果を含むオブジェクト
    @return: 200レスポンス (成功)
    '''
    per_page = 20
    query = query or request.GET['query']
    title = u'%s のレシピ検索結果' % query
    queries = query.split()
    recipes = Recipe.objects.search(queries, page=page, per_page=per_page)
    page_obj = Paginator(recipes.get('object_list'), per_page).page(page)
    links = [{'name': u'全体から検索',
        'url': reverse('gp-search', kwargs={'query': query})}]
    return render_to_response('recipes/recipes.html',
            {'page_obj': page_obj,
             'title': title,
             'links': links},
            RequestContext(request))
