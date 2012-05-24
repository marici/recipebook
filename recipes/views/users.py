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

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import (HttpResponse, HttpResponseRedirect, Http404,
    HttpResponseForbidden)
from django.template import loader, Context, RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.models import Site
from maricilib.django.shortcuts import (get_object,
    render_to_response_of_class, render_to_response_device)
from maricilib.django.decorators import getmethod, postmethod
from maricilib.django.core.paginator import Paginator
from maricilib.django.apps.taskqueue.queue import get_taskqueue
from maricilib.django.apps.taskqueue.tasks import SendEmailTask
from recipes.models import (UserProfile, FavoriteUser, Recipe, Comment,
    DailyAction, DailyScore, Karma)
from recipes import forms

recipes_per_page = 20
users_per_page = 30
comments_per_page = 20


def user_is_active_or_404(user):
    if not user.is_active:
        raise Http404


def get_profile_or_create(user):
    '''
    指定ユーザのプロファイルを返します。なければ作成します。(この関数はビュー関数ではありません。)
    '''
    try:
        profile = user.get_profile()
    except ObjectDoesNotExist:
        profile = UserProfile.objects.create(user=user)
    return profile


def send_email(template_path, context, subject, to_list):
    '''
    メールを作成し、タスクに登録します。(この関数はビュー関数ではありません。)
    '''
    t = loader.get_template(template_path)
    body = t.render(context)
    task = SendEmailTask(dict(subject=subject, body=body,
                              from_address=settings.EMAIL_FROM,
                              to_list=to_list))
    get_taskqueue().send_task(task, queue_name=settings.QUEUENAME_EMAIL)


def target_is_favorite(user, target):
    '''
    userに指定されたユーザがtargetに指定されたユーザをフェイバリットに登録していれば
    Trueを、そうでなければFalseを返します。(この関数はビュー関数ではありません。)
    '''
    if not user.is_authenticated(): return False
    fav = get_object(FavoriteUser, user=user, target=target)
    return fav is not None


@getmethod
def new(request):
    '''
    メンバー新規登録用のフォームを表示します。

    @context form: UserCreationFormインスタンス
    @return: 200レスポンス (成功。フォームを表示)
    '''
    userform = forms.UserCreationForm()
    return render_to_response_device(request, 'registration/new_form.html',
            {'form': userform}, RequestContext(request))


@postmethod
def new(request):
    '''
    メンバーを作成します。
    forms.UserCreationFormで定義された値を受け取ります。
    必須項目はNewRecipeFormを参照してください。
    作成が成功した場合、メール送信通知ページを表示します。

    作成に成功した場合、Contextで返されるUserインスタンスは以下の状態になっています。
    email: フォームから渡された値
    username: emailの@を_に置換した文字列
    first_name: ニックネーム
    is_active: False

    Contextで返されるUserProfileインスタンスは以下の状態になっています。
    birth_year, prefecture: フォームから渡された値
    is_female: フォームでgenderをfemaleとしていればTrue

    @context created_user: Userインスタンス
    @context profile: UserProfileインスタンス
    @return: 200レスポンス (成功)
    @return: 200レスポンス (バリデートに失敗。フォームを再表示)
    '''
    form = forms.UserCreationForm(request.POST)
    if not form.is_valid():
        return render_to_response_device(request, 'registration/new_form.html',
            {'form': form}, RequestContext(request))
    user = form.save(commit=False)
    user.is_active = False
    user.save()
    profile = UserProfile.objects.create_pending_user(user=user,
            alter_email=user.email,
            **(form.get_profile_dict()))
    email_validation_url(request, user, profile)
    d = {'created_user': user, 'profile': profile}
    return render_to_response_device(request,
            'registration/new_sent_email.html', d, RequestContext(request))


def email_validation_url(request, user, profile):
    '''
    メールアドレス確認用のメールを送信します。(この関数はビュー関数ではありません。)
    '''
    site = Site.objects.get_current()
    validation_url = request.build_absolute_uri(
                            reverse('recipes-users-validate',
                            kwargs={'key': profile.validation_key}))
    c = Context({'created_user': user, 'profile': profile,
                 'validation_url': validation_url})
    subject = u'[%s] メンバー登録確認メール' % site.name
    send_email('recipes/email/validation.txt', c, subject, [user.email])


def validate(request, key=None):
    '''
    ユーザをアクティベートします。
    指定されたkeyを持つUserProfileインスタンスを検索し、そのuserインスタンスの
    is_activeをTrueに設定します。
    UserProfileインスタンスのkey_issued_atが2日以上古い場合、403エラーを返します。

    @context created_user: アクティベートされたユーザ
    @context profile: ユーザプロファイル
    @param key: バリデーションキー
    @return: 200レスポンス (成功。)
    @return: 403レスポンス (UserProfileインスタンスのkey_issued_atが2日以上古い場合)
    @return: 404レスポンス (該当のUserProfileインスタンスが存在しない場合)
    '''
    profile = get_object_or_404(UserProfile, validation_key=key)
    if not profile.validate(key):
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    profile.disable_validation_key()
    profile.save()
    user = profile.user
    user.is_active = True
    user.save()
    d = {'created_user': user, 'profile': profile}
    return render_to_response_device(request, 'registration/new_success.html',
        d, RequestContext(request))


@getmethod
@login_required
def inactivate(request):
    '''
    退会用確認画面を表示します。

    @return: 302レスポンス (ログインしていない場合。ログインページへ)
    '''
    return render_to_response('registration/inactivate_confirm.html',
            {}, RequestContext(request))


@postmethod
@login_required
def inactivate(request):
    '''
    ユーザを退会させ、ログアウトさせます。

    @return: 404レスポンス (ログインしていない場合)
    @return: 200レスポンス (成功)
    '''
    request.user.is_active = False
    request.user.save()
    auth.logout(request)
    return render_to_response('registration/inactivate_done.html',
            {}, RequestContext(request))


def show(request, user_id=None):
    '''
    指定されたユーザのプロフィールやレシピなどを表示します。

    @param user_id: ユーザID
    '''
    user = get_object_or_404(User, pk=user_id)
    user_is_active_or_404(user)
    profile = get_profile_or_create(user)
    is_favorite = target_is_favorite(request.user, user)
    popular_recipes = Recipe.objects.get_popular_recipes(user)[: 5]
    recent_recipes = Recipe.objects.get_recent_recipes(user)[: 10]
    favorite_recipes = Recipe.objects.favorite_recipes(user)[: 5]
    favorite_users = FavoriteUser.objects.get_favorite_users(user)
    u_and_p = zip_profile(favorite_users, favorite_users.values('pk').query)
    d = {'homeuser': user, 'profile': profile, 'is_favorite': is_favorite,
         'popular_recipes': popular_recipes, 'recent_recipes': recent_recipes,
         'favorite_recipes': favorite_recipes,
         'favorite_user_profiles': u_and_p}
    return render_to_response('recipes/user.html',
            d, RequestContext(request))


@login_required
def show_home(request):
    '''
    アクセスユーザのホーム画面を表示します。

    @return: 403レスポンス (ログインしていない場合)
    '''
    user = request.user
    profile = get_profile_or_create(user)
    recent_recipes = Recipe.objects.get_recent_recipes(user,
            allow_draft=True)[:10]
    comments = Comment.objects.get_owner_comments(user)[: 5]
    fav_user_actions = FavoriteUser.objects.get_favorite_user_actions(
            user)[:10]
    d = {'profile': profile,
         'recent_recipes': recent_recipes,
         'comments': comments,
         'favorite_user_actions': fav_user_actions}
    if not DailyAction.objects.is_done(user, user, 'login'):
        Karma.add_karma(user, Karma.act_login, profile)
    return render_to_response('recipes/home.html',
            d, RequestContext(request))


def get_user_links(user):
    '''
    ユーザページへのリンクを表す辞書のリストを返します。 (この関数はビュー関数ではありません)
    '''
    return [{'url': reverse('recipes-users-show',
                            kwargs={'user_id': user.id}),
              'name': u'%s さん' % user.first_name}]


def show_recipe_list(request, user_id=None, page=1):
    '''
    指定されたユーザのレシピ一覧をpublished_atの新しい順に表示します。
    下書き(is_draft == True)は表示されません。

    @param user_id: ユーザID
    @param page: 表示ページ
    @return: 404レスポンス (ユーザが存在しない、または is_active == Falseの場合)
    '''
    user = get_object_or_404(User, pk=user_id)
    user_is_active_or_404(user)
    recipes = Recipe.objects.get_recent_recipes(user,
                        allow_draft=(request.user == user))
    page_obj = Paginator(recipes, recipes_per_page).page(page)
    return render_to_response('recipes/recipes.html',
            {'title': u'%s さんのレシピ' % user.first_name,
            'page_obj': page_obj, 'links': get_user_links(user)},
            RequestContext(request))


@getmethod
@login_required
def edit_profile(request):
    '''
    プロフィール編集フォームを表示します。

    @return: 302レスポンス (ログインしていない場合)
    '''
    user = request.user
    profile = get_profile_or_create(user)
    profile_form = forms.UserProfileForm(instance=profile,
            initial={'prefecture': profile.prefecture,
            'first_name': user.first_name,
            'last_name': user.last_name})
    d = {'profile': profile, 'profile_form': profile_form}
    return render_to_response('recipes/user_setting_form.html',
                              d, RequestContext(request))


@postmethod
@login_required
def edit_profile(request):
    '''
    プロフィールデータを変更します。
    項目はUserProfileFormの定義に従います。

    @return: 200レスポンス (成功、失敗いずれも)
    '''
    user = request.user
    profile = user.get_profile()
    profile_form = forms.UserProfileForm(request.POST, request.FILES,
                                         instance=profile)
    if not profile_form.is_valid():
        d = {'profile': profile, 'profile_form': profile_form}
        return render_to_response('recipes/user_setting_form.html',
            d, RequestContext(request))
    profile = profile_form.save()
    nickname = request.POST.get('nickname')
    if user.first_name != nickname:
        user.first_name = nickname
        user.save()
    messages.add_message(request, messages.INFO, u'設定を変更しました')
    return HttpResponseRedirect(reverse('recipes-users-edit-profile'))


@postmethod
@login_required
def add_favorite_user(request, user_id=None):
    '''
    指定されたIDのユーザをログインユーザのフェイバリットに登録します。
    指定IDのユーザを除くユーザだけが作成を行うことができます。(user!=request.user)

    JSONで返されるFavoriteUserインスタンスは以下の状態になっています。
    user: ログインユーザ
    target: 指定されたIDのUserインスタンス

    @param user_id: ユーザID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (指定されたユーザがログインユーザの場合)
    @return: 404レスポンス (指定されたIDのユーザが存在しない場合)
    @return: 200レスポンス (成功。FavoriteUserインスタンスをJSONで出力)
    '''
    target = get_object_or_404(User, pk=user_id)
    user_is_active_or_404(target)
    if target == request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    if not FavoriteUser.objects.reach_limit(request.user):
        try:
            fav = FavoriteUser.objects.get(user=request.user, target=target)
        except:
            fav = FavoriteUser.objects.create(user=request.user, target=target)
        data = serializers.serialize('json', [fav])
        return HttpResponse(data, mimetype='application/javascript')
    else:
        message = (u'申し訳ありません。'
            u'フェイバリットメンバーにできるのは%s人までです。')\
            % FavoriteUser.objects.limit
        request.user.message_set.create(message=message)
        return render_to_response_of_class(HttpResponseForbidden, '403.html')


@postmethod
@login_required
def remove_favorite_user(request, user_id=None):
    '''
    指定されたIDのユーザをログインユーザのフェイバリットから削除します。
    該当のFavoriteUserインスタンスを作成したユーザだけが削除を行うことが出来ます。
    成功した場合、削除されたFavoriteRecipeインスタンスがJSONで返ります。

    @param user_id: ユーザID
    @return: 302レスポンス (ログインページへ。ログインしていない場合)
    @return: 403レスポンス (FavoriteUserインスタンスを作成していない場合)
    @return: 404レスポンス (指定されたIDのユーザをフェイバリットにしていない場合)
    @return: 200レスポンス (成功。FavoriteUserインスタンスをJSONで出力)
    '''
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')
    try:
        fav = FavoriteUser.objects.get(user=request.user, target=target)
        data = serializers.serialize('json', [fav])
        fav.delete()
    except:
        raise Http404
    return HttpResponse(data, mimetype='application/javascript')


def show_favorite_recipes(request, user_id=None, page=1):
    '''
    指定されたユーザのフェイバリットレシピを一覧表示します。

    @param user_id: ユーザID
    @param page: 表示ページ
    @context page_obj: object_listにクエリセットを含むPageオブジェクト
    @return: 404レスポンス (指定ユーザが存在しない、またはis_active == Falseの場合)
    @return: 200レスポンス (成功)
    '''
    user = get_object_or_404(User, pk=user_id)
    user_is_active_or_404(user)
    fav_recipes = Recipe.objects.favorite_recipes(user)
    page_obj = Paginator(fav_recipes, recipes_per_page).page(page)
    links = get_user_links(user)
    links.append(dict(name=u'%s さんのフェイバリットメンバー' % user.first_name,
                       url=reverse('recipes-users-favorite-users-show',
                                   kwargs={'user_id': user.id})))
    d = {'title': u'%s さんのフェイバリットレシピ' % user.first_name,
         'page_obj': page_obj, 'links': links}
    return render_to_response('recipes/recipes.html',
            d, RequestContext(request))


def show_favorite_users(request, user_id=None, page=1):
    '''
    指定されたユーザのフェイバリットメンバーを一覧表示します。

    @param user_id: ユーザID
    @param page: 表示ページ
    @context favorite_users_and_profiles: ユーザおよびプロファイルを含む辞書のリスト
    @return: 404レスポンス (指定ユーザが存在しない、またはis_active == Falseの場合)
    @return: 200レスポンス (成功)
    '''
    user = get_object_or_404(User, pk=user_id)
    user_is_active_or_404(user)
    fav_user_ids = FavoriteUser.objects.filter(user=user).values(
            'target_id').query
    fav_users = User.objects.filter(pk__in=fav_user_ids)
    u_and_p = zip_profile(fav_users, fav_users.values('pk').query)
    links = get_user_links(user)
    links.append({'name': u'%s さんのフェイバリットレシピ' % user.first_name,
                  'url': reverse('recipes-users-favorite-recipes-show',
                                kwargs={'user_id': user.id})})
    d = {'homeuser': user, 'favorite_users_and_profiles': u_and_p,
         'links': links}
    return render_to_response('recipes/favorite_users.html',
            d, RequestContext(request))


@login_required
def show_owner_comments(request, only_not_moderated=False, page=1):
    '''
    ログインユーザのレシピにつけられたコメント一覧を表示します。

    @param only_not_moderated: 未承認のコメントのみを指定する場合True
    @param page: 表示ページ
    @return: 302レスポンス (ログインしていない場合。ログインページへ。)
    '''
    page = page or 1  # Noneが渡ることがあるため
    qs = Comment.objects.filter(owner=request.user)
    if only_not_moderated:
        qs = qs.filter(is_moderated=False)
    page_obj = Paginator(qs.order_by('-created_at'),
                         comments_per_page).page(page)
    d = {'only_not_moderated': only_not_moderated, 'page_obj': page_obj}
    return render_to_response('recipes/comments.html',
            d, RequestContext(request))


@login_required
@getmethod
def change_email(request):
    '''
    メールアドレス変更フォームを表示します。
    @return: 302レスポンス (ログインしていない場合。ログインページへ。)
    '''
    return render_change_email_form(request, forms.EmailChangeForm())


def render_change_email_form(request, form):
    d = {'form': form,
         'title': u'メールアドレスの変更',
         'focus_id': 'id_email',
         'text': u'新しいメールアドレスを入力してください。',
         'submit_text': u'変更'}
    return render_to_response('base_form.html',
                              d, RequestContext(request))


@login_required
@postmethod
def change_email(request):
    '''
    メールアドレス変更を登録します。
    POSTすべき内容はEmailChangeFormに定義された項目に従います。
    変更完了のためにアクセスすべきURLを作成し、新しいアドレスにメールを送信します。

    @return: 302レスポンス (ログインしていない場合。ログインページへ。)
    @return: 200レスポンス (成功またはフォーム内容が不正な場合)
    '''
    form = forms.EmailChangeForm(request.POST)
    if form.is_valid():
        new_email = form.cleaned_data['email']
        profile = request.user.get_profile()
        profile.change_email(new_email)
        profile.save()
        email_change_email(request, request.user, profile)
        message = u'%s にメールを送信しました。\n' % new_email + \
            u'メールに含まれるURLをクリックすると、変更が完了します。'
        d = {'title': u'メールアドレスの変更',
             'text': message}
        return render_to_response('base_message.html',
                                  d, RequestContext(request))
    else:
        return render_change_email_form(request, form)


def email_change_email(request, user, profile):
    '''
    メールをタスクに登録します。 (この関数はビュー関数ではありません)
    '''
    site = Site.objects.get_current()
    validation_url = request.build_absolute_uri(
        reverse('recipes-users-validate-email',
        kwargs={'user_id': user.id,
                'key': profile.validation_key}))
    send_email('registration/email/change_email.txt',
               Context({'user': user, 'validation_url': validation_url}),
               u'[%s] アドレス変更確認メール' % site.name,
               [profile.pending_email])


def validate_change_email(request, user_id=None, key=None):
    '''
    メールアドレス変更を行います。

    @param user_id: 変更を行うユーザのID
    @param key: 変更のためのバリデーションキー
    @return: 403レスポンス (キーが正しくない場合)
    @return: 200レスポンス (成功)
    '''
    user = get_object_or_404(User, pk=user_id)
    profile = user.get_profile()
    if profile.validate(key):
        profile.disable_validation_key()
        profile.save()
        user.email = profile.pending_email
        user.username = forms.email_to_username(user.email)
        user.save()
        d = {'title': u'メールアドレスの変更完了',
             'text': u'メールアドレスの変更が完了しました。'}
        return render_to_response('base_message.html',
                                  d, RequestContext(request))
    else:
        return render_to_response_of_class(HttpResponseForbidden, '403.html')


@getmethod
def login(request, template_name='registration/login.html'):
    '''
    ログインフォームを表示します。
    '''
    d = {'form': forms.AuthenticationForm(),
        'next': request.REQUEST.get('next', '')}
    return render_to_response(template_name, d, RequestContext(request))


@postmethod
def login(request, template_name=None):
    '''
    アクセスユーザのログインを行います。
    項目はAuthenticationFormの定義に従います。

    @return: 200レスポンス (フォーム内容が不正な場合)
    @return: 302レスポンス (成功。ホーム画面またはnextで指定されたパスへ)
    '''
    form = forms.AuthenticationForm(request.POST)
    if form.is_valid():
        user = form.get_user()
        if user is not None and user.is_active:
            auth.login(request, user)
            redirect_to = request.REQUEST.get('next', '')
            if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            return HttpResponseRedirect(redirect_to)
    return render_to_response('registration/login.html', {'form': form},
                              RequestContext(request))


def show_active_users(request):
    '''
    アクティブメンバーの一覧を表示します。
    アクティブメンバーとは、最近五週間でDailyScoreの上位に入ったユーザのことです。

    @context users_and_profiles: ユーザおよびプロファイルを含む辞書のリスト
    @return: 200レスポンス (成功)
    '''
    u_and_p = get_active_users_and_profiles()
    return render_to_response('recipes/active_users.html',
                              {'users_and_profiles': u_and_p},
                              RequestContext(request))


def get_active_users_and_profiles():
    '''
    アクティブメンバーの一覧を取得します。
    この関数はビュー関数ではありません。
    '''
    from datetime import datetime, timedelta
    u_and_p = cache.get('recipes_users_show_active_users')
    if u_and_p is None:
        a_week_ago = datetime.now() - timedelta(weeks=5)
        users = DailyScore.objects.get_ranked_objects(User, a_week_ago,
                limit=20)
        u_and_p = zip_profile(users, users)
        cache.set('recipes_users_show_active_users', u_and_p)
    return u_and_p


def zip_profile(users, user_ids):
    '''
    渡されたユーザIDのリストからプロファイルを検索し、該当ユーザとともに辞書に格納し、
    辞書のリストを返します。 (この関数はビュー関数ではありません)
    '''
    profiles = UserProfile.objects.filter(user__in=user_ids)
    d = {}
    for profile in list(profiles):
        d[profile.user_id] = profile
    return [{'user': user, 'profile': d.get(user.id, None)}
            for user in users]
