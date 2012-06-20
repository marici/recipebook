# -*- coding: utf-8 -*-

import os
import plistlib
from uuid import uuid4 as uuid
from django.core import serializers
from django.contrib import auth
from django.utils import simplejson
from django.http import HttpResponse
from django.template import RequestContext
from django_plist import render_dictionary
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.csrf import csrf_exempt
from django import forms
from recipes.models.service import *
from django.conf import settings
from recipes.models import (Contest, Recipe, Direction, UserProfile)

json_serializer = serializers.get_serializer("json")()


class RecipeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(RecipeForm, self).__init__(*args, **kwargs)

    data = forms.CharField()
    answers = forms.CharField(required=False)
    id = forms.IntegerField()
    contest_id = forms.IntegerField(required=False)

    def make_recipe(self, FILES, model):
        self.is_valid()
        data = self.cleaned_data['data'][0]
        answers = self.cleaned_data['answers']
        direction_list = self.directions_set_add(data['directions'],
                FILES, u'users/direction')
        rel_path = self.save_photo(data, FILES,
                        u'users/recipe')
        user = User.objects.get(id=self.cleaned_data['id'])
        self.pop_needless_data(data)
        recipe = model(user=user, **data)
        self.add_ingredients(recipe, data['ingredients'])
        contest = self.cleaned_data['contest_id']
        if contest:
            contest_obj = Contest.objects.get(id=contest)
            recipe.contest = contest_obj
        if data['photo']:
            try:
                recipe.photo = rel_path
            except:
                raise
        if answers:
            try:
                recipe = self.add_answer(recipe, answers)
            except:
                raise
        try:
            recipe.save()
            self.add_recipe_direction(direction_list, recipe)
        except:
            raise
        return recipe.id

    def add_answer(self, recipe, answers):
        i = 1
        for answer in answers:
            try:
                setattr(recipe, 'answer_' + str(i), answer)
                i = int(i)
                i += 1
            except:
                raise
        return recipe

    def pop_needless_data(self, data):
        del data['directions']
        del data['preparation']

    def add_ingredients(self, recipe, array):
        names = []
        quantities = []
        for ar in array:
            names.append(ar[0].encode('utf-8'))
            quantities.append(ar[1].encode('utf-8'))
        recipe.encode_ingredients(names, quantities)

    def add_recipe_direction(self, direction_list, recipe):
        for direction in direction_list:
            try:
                direction.recipe = recipe
            except:
                raise
            try:
                direction.save()
            except:
                raise

    def clean_data(self):
        data = self.data['data']
        html = self.encode_html(data)
        parse_data = self.parse_plist(html)
        return parse_data

    def clean_answers(self):
        try:
            answers = self.data['answers']
        except:
            answers = None
            parse_data = None
        if answers:
            html = self.encode_html(answers)
            parse_data = self.parse_plist(html)
        return parse_data

    def parse_plist(self, post_data):
        parse_data = plistlib.readPlistFromString(post_data)
        return parse_data

    def encode_html(self, html):
        html = html.encode('utf-8')
        return html

    def directions_set_add(self, directions, file_name, path):
        direction_list = []
        for direction in directions:
            rel_path = self.save_photo(direction, file_name, path)
            direction_text = direction['text']
            direction_number = direction['number']
            direc_data = {'text': direction_text, 'number': direction_number,
                    'photo': rel_path}
            direc_instance = Direction(**direc_data)
            direction_list.append(direc_instance)
        return direction_list

    def direction_delete_and_add(self, directions, file_name, path, recipe):
        direction = Direction.objects.filter(recipe=recipe)
        direction.delete()
        direction_list = self.directions_set_add(directions, file_name, path)
        self.add_recipe_direction(direction_list, recipe)

    def get_photo(self, obj, files):
        #photoが入っているか確かめる
        photo_key = unicode(obj['photo']) if getattr(obj, 'photo') else None
        if photo_key:
            try:
                photo = files[photo_key]
            except:
                photo = None
        else:
            photo = None
        return photo

    def get_paths(self, photo, path):
        #パスを取得する
        rel_path = self.get_media_path(photo.name, path)
        full = os.path.join(settings.MEDIA_ROOT, path)
        abs_path = self.get_media_path(photo.name, full)
        return rel_path, abs_path

    def save_photo(self, obj, files, path):
        #保存するパスを知る必要がある
        #保存するファイルをしる必要がある
        #ファイルを保存する
        photo = self.get_photo(obj, files)
        if photo:
            rel_path, abs_path = self.get_paths(photo, path)
            destination = open(abs_path, 'wb')
            if photo.multiple_chunks():
                for chunk in photo.chunks():
                    destination.write(chunk)
            else:
                photo_image = photo.read()
                destination.write(photo_image)
            return rel_path

    def get_media_path(self, filename, path):
        return os.path.join(path,
                    u'%s%s' % (uuid.uuid4(), os.path.splitext(filename)[1]))

    def edit_recipe(self, recipe_id, FILES, model):
        self.is_valid()
        data = self.cleaned_data['data'][0]
        recipe = model.objects.get(id=recipe_id)
        self.direction_delete_and_add(data['directions'],
                FILES, u'users/direction', recipe)
        recipe = self.update_recipe(recipe, data)
        return recipe.id

    def update_recipe(self, recipe, clean_data):
        name = clean_data['name']
        introduction = clean_data['introduction']
        tips = clean_data['tips'] if clean_data['tips'] else None
        is_draft = clean_data['is_draft']
        #feeling = clean_data['feeling']
        num_people = clean_data['num_people']
        recipe.name = name if name else recipe.name
        recipe.introduction = (introduction if introduction
    else recipe.introduction)
        recipe.tips = tips if tips else recipe.tips
        recipe.is_draft = is_draft if is_draft else recipe.is_draft
        #recipe.feeling = feeling if feeling else recipe.feeling
        recipe.num_people = num_people if num_people else recipe.num_people
        recipe.save()
        return recipe


def contest_api(request, output_format='JSON', model=Contest):
    '''
    コンテスト一覧に使用するためのAPI
    '''
    contests = model.objects.get_current_contests()
    #今開催されているコンテストを辞書形式でとってくる
    contest_list = []
    for contest in contests:
        data = contest.to_dict()
        contest_list.append(data)
    if output_format == 'plist':
        text = render_dictionary(contest_list)
    else:
        text = simplejson.dumps(contest_list, ensure_ascii=False)
    return HttpResponse(text)


def contest_detail_api(request, contest_id=None,
        output_format='JSON', model=Contest):
    '''
    コンテスト詳細に個別IDに応じて引き出したURLに飛ぶためのAPI
    '''
    contest = get_object_or_404(model, pk=contest_id) if contest_id else None
    if contest:
        data = contest.to_dict()
        if output_format == 'plist':
            text = render_dictionary(data)
        else:
            text = simplejson.dumps(data, ensure_ascii=False)
            #json_serializerはクエリセットをJSONにしてくれる。
    else:
        text = None
    return HttpResponse(text)


def recipe_list_api(request, user_id=None, output_format='JSON', model=Recipe):
    '''
    ユーザにひもづいたレシピをとってきて、コンテストに登録していなかったら
    コンテストというキー自体を削除してからJSONおよびPlistに変換して
    表示する
    '''
    #対応するユーザIDによってレシピを取得する。
    #取得したレシピを辞書にもどす。
    #辞書データをplistまたはjsonにする(これはviewの仕事)
    #返答を返す。(viewの仕事)
    recipes = model.objects.select_related().filter(
            user__pk=user_id) if user_id else None
    recipe_list = []
    for recipe in recipes:
        data = recipe.to_dict()
        recipe_list.append(data)
    if output_format == 'plist':
        text = render_dictionary(recipe_list)
    else:
        '''
        ここでは、wadofstuff-django-serializersを使っています。
        また、wadofstuss-django-serializer内の base.pyで元々importされているものを
        #try:
        #    from cStringIO import StringIO
        #except ImportError:
        #    from StringIO import StringIO
        上のようにコメントアウトし、
        from StringIO import StringIO
        をimportしています。これは、cStringIOがユニコード文字列を扱えないからです
        '''
        text = simplejson.dumps(recipe_list, ensure_ascii=False)
    return HttpResponse(text)


@csrf_exempt
def make_new_recipe(request, model=Recipe):
    try:
        if request.POST:
            recipe = RecipeForm(request.POST)
            try:
                recipe_id = recipe.make_recipe(request.FILES, model)
                return HttpResponse(recipe_id)
            except:
                raise
        return render_to_response('recipes/multipart-sample.html',
                context_instance=RequestContext(request))
    except Exception, e:
        raise


@csrf_exempt
def edit_recipe(request, recipe_id=None, model=Recipe):
    try:
        if request.POST and recipe_id:
            form = RecipeForm(request.POST)
            success = form.edit_recipe(recipe_id, request.FILES, model)
            return HttpResponse(success)
    except:
        raise
    return render_to_response('recipes/multipart-sample2.html',
            {'d': recipe_id}, context_instance=RequestContext(request))


@csrf_exempt
def login_api(request, output_format='JSON'):
    try:
        if request.method == 'POST':
            form = AuthenticationForm(request.POST)
            if form.is_valid():
                user = form.get_user()
                if  user is not None and user.is_active:
                    auth.login(request, user)
                    text = get_auth_info(user, output_format)
                    return HttpResponse(text)
        else:
            form = AuthenticationForm()
    except:
        raise
    return render_to_response('recipes/api_login.html',
            {'form': form, 'output_format': output_format},
            context_instance=RequestContext(request))


def outer_service_login_api(request, output_format='JSON'):
    if request.method == 'POST':
        token = getattr(request.POST, 'token')
        if token:
            pass
    return render_to_response('recipes/api_login_outside.html',
            {'form': form},
            context_instance=RequestContext(request))


def get_auth_info(user, output_format):
    user_info = {}
    user_info['username'] = user.username
    user_info['first_name'] = user.first_name
    user_info['last_name'] = user.last_name
    user_info['user_id'] = user.id
    profile = UserProfile.objects.get(user=user)
    user_info['userprofile'] = profile.to_dict()
    if output_format == 'plist':
        text = render_dictionary(user_info)
    else:
        text = simplejson.dumps(user_info, ensure_ascii=False)
    return text
