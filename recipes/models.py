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
import os, itertools, uuid
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
from recipebook.maricilib.django.shortcuts import get_object
from recipebook.maricilib.django.db.models.base import S3SyncModelBase
from recipebook.maricilib.django.db.models import fields
from recipebook.maricilib.django.apps.taskqueue import register_task
from recipebook.maricilib.django.apps.taskqueue.tasks import SyncS3Task, DeleteS3Task
from recipebook.maricilib.django.apps.taskqueue.queue import get_taskqueue
from recipebook.maricilib.django.apps.search import register_index
from recipebook.maricilib.django.apps.daily.models import DailyAction, DailyScore
import managers, scores

class Karma(object):
    """
    ユーザの操作とそれによるポイント定義
    """
    act_login = "act_login"
    act_favorite = "act_favorite"
    act_vote = "act_vote"
    act_comment = "act_comment"
    act_create_recipe = "act_recipe"
    actions = {act_login:1, act_favorite:1, act_vote:2,
               act_comment:2, act_create_recipe:3}

    @classmethod
    def add_karma(cls, user, action, profile=None, save=True):
        if profile is None:
            profile = user.get_profile()
        profile.add_karma(action=Karma.act_favorite)
        if save:
            profile.save()
    
# =======================================================
# マスタデータ
# =======================================================

class IngredientCategory(models.Model):
    """
    野菜、夏の食べ物などの食材カテゴリ
    """
    class Meta:
        verbose_name = verbose_name_plural = u"食材カテゴリ"
        
    name = models.CharField(max_length=20)
    photo = models.ImageField(u"写真",
                              upload_to=u"public/ingcategory", 
                              null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    

class Ingredient(models.Model):
    """
    茄子、豚肉などの代表的な食材
    """
    class Meta:
        verbose_name = verbose_name_plural = u"食材"
        
    name = models.CharField(max_length=20)
    photo = models.ImageField(u"写真",
                              upload_to=u"public/ingredient", 
                              null=True, blank=True)
    categories = models.ManyToManyField("IngredientCategory")
    
    def __unicode__(self):
        return self.name


class DishCategory(models.Model):
    """
    肉料理、煮物などの料理カテゴリ
    """
    class Meta:
        verbose_name = verbose_name_plural = u"料理カテゴリ"
        
    name = models.CharField(max_length=20)
    photo = models.ImageField(u"写真",
                              upload_to=u"public/dishcategory", 
                              null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    

class Dish(models.Model):
    """
    ハンバーグ、クリームシチューなどの代表的な料理
    """
    class Meta:
        verbose_name = verbose_name_plural = u"料理"
        
    name = models.CharField(max_length=20)
    photo = models.ImageField(u"写真",
                              upload_to=u"public/dish", 
                              null=True, blank=True)
    categories = models.ManyToManyField("DishCategory")
    
    def save(self, force_insert=False, force_update=False):
        dish_registry.clear()
        super(Dish, self).save(force_insert, force_update)
        
    def __unicode__(self):
        return self.name


class Feeling(models.Model):
    """
    「子供が喜ぶ」「ヘルシー」などの代表的なフィーリング
    """
    class Meta:
        verbose_name = verbose_name_plural = u"フィーリング"
        
    name = models.CharField(max_length=20)
    photo = models.ImageField(u"写真",
                              upload_to=u"public/feeling", 
                              null=True, blank=True)
    
    def save(self, force_insert=False, force_update=False):
        feeling_registry.clear()
        super(Feeling, self).save(force_insert, force_update)
        
    def __unicode__(self):
        return self.name

# =======================================================
# 運営しながら作成するデータ
# =======================================================

class FarmProducer(models.Model):
    """
    食材生産者
    """
    class Meta:
        verbose_name = verbose_name_plural = u"食材生産者"
        
    name = models.CharField(u"名前", max_length=50)
    introduction = models.TextField(u"紹介文")
    photo = models.ImageField(u"写真",
                              upload_to=u"public/producer", 
                              null=True, blank=True)
    url = models.URLField(u"URL", null=True, blank=True)
    
    def __unicode__(self):
        return self.name


class Contest(models.Model):
    """
    募集するお題
    """
    class Meta:
        verbose_name = verbose_name_plural = u"お題"

    objects = managers.ContestManager()

    name = models.CharField(max_length=50,
            verbose_name=u"タイトル")
    ingredients = models.ManyToManyField(Ingredient,
            verbose_name=u"食材",
            null=True, blank=True)
    dish = models.ForeignKey(Dish,
            verbose_name=u"料理",
            null=True, blank=True)
    feeling = models.ForeignKey(Feeling,
            verbose_name=u"フィーリング",
            null=True, blank=True)
    description = models.TextField(u"説明")
    image = fields.ResizedImageField(u"イメージ",
            max_width=500, max_height=500,
            upload_to=u"public/contest/",
            null=True, blank=True)
    producer = models.ForeignKey(FarmProducer,
                                 verbose_name=u"生産者", 
                                 null=True, blank=True)
    royalty = models.PositiveSmallIntegerField(u"ロイヤルティ率",
                                               default=3)
    created_at = models.DateTimeField(u"作成日",
            auto_now_add=True)
    published_at = models.DateTimeField(u"募集開始日")
    closed_at = models.DateTimeField(u"募集締切日")
    finished_at = models.DateTimeField(u"審査結果発表日")
    is_reviewing = models.BooleanField(u"審査中", default=False)
    is_finished = models.BooleanField(u"審査完了", default=False)
    comment = models.TextField(u"選評", null=True, blank=True)
    rp_kwargs = {"upload_to":"public/contest/review", "null":True, "blank":True,
                 "max_width":300, "max_height":300}
    reviewing_photo1 = fields.ResizedImageField(u"審査写真1", **rp_kwargs)
    reviewing_photo2 = fields.ResizedImageField(u"審査写真2", **rp_kwargs)
    reviewing_photo3 = fields.ResizedImageField(u"審査写真3", **rp_kwargs)
    reviewing_photo4 = fields.ResizedImageField(u"審査写真4", **rp_kwargs)
    reviewing_photo5 = fields.ResizedImageField(u"審査写真5", **rp_kwargs)
    
    def __unicode__(self):
        return self.name
    
    def is_published(self):
        return self.published_at <= datetime.now()

    def is_closed(self, now=None):
        now = now or datetime.now()
        return self.closed_at <= now
    
    def is_really_finished(self):
        now = datetime.now()
        return self.is_finished and self.finished_at and self.finished_at <= now
    
    def get_left_days(self):
        return (self.closed_at - datetime.now()).days
    left_days = property(get_left_days)

    def open_recipes(self):
        return self.recipe_set.filter(is_draft=False)
    
    def get_new_recipes(self, number=10):
        qs = self.recipe_set.filter(is_draft=False).order_by("-created_at")
        return list(qs[:number])
    
    def get_featured_recipes(self, number=3):
        qs = self.recipe_set.filter(is_draft=False).filter(score__lt=10).order_by("-score")
        return list(qs[:number])
    featured_recipes = property(get_featured_recipes)

    def get_awarded_recipes(self):
        return list(self.recipe_set.filter(is_awarded=True))
    awarded_recipes = property(get_awarded_recipes)
        
    def get_awarded_recipe(self):
        recipes = self.get_awarded_recipes()
        return recipes[0] if recipes else None
    awarded_recipe = property(get_awarded_recipe)
        
    def __need_add_index__(self):
        now = datetime.now()
        return self.published_at <= now
    
    def __need_delete_index__(self):
        return False
    
    def __indexdoc__(self):
        if len(feeling_registry) == 0: update_feeling_registry()
        if len(dish_registry) == 0: update_dish_registry()
        d = {"name":self.name,
             "description":self.description,
             "dish":dish_registry.get(self.dish_id, ""),
             "feeling":feeling_registry.get(self.feeling_id, ""),
             "ingredients":" ".join([ ing.name for ing in self.ingredients.all() ])
        }
        return d
    

class ReviewedContest(models.Model):
    """
    審査中のお題
    """
    class Meta:
        verbose_name = verbose_name_plural = u"審査中のお題"

    contest = models.ForeignKey(Contest, verbose_name=u"お題",
                                null=True, blank=True)
    name = models.CharField(u"タイトル", max_length=20)
    
    def __unicode__(self):
        return self.name
    
# =======================================================
# ユーザが作成するデータ
# =======================================================

class UserProfile(models.Model):
    __metaclass__ = S3SyncModelBase
    
    class Meta:
        verbose_name = verbose_name_plural = u"メンバープロファイル"
        
    objects = managers.UserProfileManager()
    
    user = models.ForeignKey(User, verbose_name=u"メンバー", unique=True, 
                             editable=False)
    validation_key = models.CharField(u"バリデーションキー", max_length=50,
                                      null=True, blank=True, db_index=True,
                                      editable=False)
    key_issued_at = models.DateTimeField(u"キー発行日時", null=True, blank=True,
                                         editable=False)
    recipe_token = models.CharField(u"投稿トークン", max_length=50,
                                    null=True, blank=True, editable=False)
    token_issued_at = models.DateTimeField(u"トークン発行日時", null=True, blank=True,
                                           editable=False)
    pending_email = models.EmailField(u"変更メールアドレス", null=True, blank=True,
                                    editable=False)
    alter_email = models.EmailField(u"代替メールアドレス", null=True, blank=True,
                                    editable=False)
    is_female = models.BooleanField(u"性別 (女性)", default=True)
    birth_year = models.PositiveIntegerField(u"生年", null=True, blank=True)
    prefecture = models.CharField(u"住所 (県)", max_length=50, 
                                  null=True, blank=True)
    profile_text = models.TextField(u"プロフィール", null=True, blank=True)
    blog_url = models.URLField(u"ブログURL", null=True, blank=True)
    icon = fields.S3SyncResizedImageField(u"アイコン", 
                             upload_to=lambda i, f: i.make_icon_filepath(f),
                             max_width=100, max_height=100,
                             null=True, blank=True)
    deny_comment = models.BooleanField(u"コメント拒否", default=False)
    deny_mail_magazine = models.BooleanField(u"お知らせメール拒否", default=False)
    karma = models.IntegerField(u"カルマ", editable=False, default=0)
    level = models.IntegerField(u"レベル", editable=False, default=1)
    vote_point = models.PositiveIntegerField(u"投票ポイント", editable=False,
                                             default=1)
    created_at = models.DateTimeField(u"作成日", auto_now_add=True)
    
    def make_icon_filepath(self, filename):
        ext = os.path.splitext(filename)[1]
        path = "users/icon/%s%s" % (self.user.id, ext)
        self.icon.storage.delete(path)
        if self.icon_s3:
            get_taskqueue().send_task(DeleteS3Task({"name":path}),
                                      settings.QUEUENAME_SENDS3)
        self.icon_s3 = None
        self.icon_s3_sync = False
        get_taskqueue().send_task(SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3)
        return path
    
    def change_email(self, new_email):
        self.pending_email = new_email
        self.generate_validation_key()
        
    def generate_validation_key(self):
        self.validation_key = str(uuid.uuid4())
        self.key_issued_at = datetime.now()
        
    def disable_validation_key(self):
        self.validation_key = None
        self.key_issued_at = None
        
    def validate(self, key):
        if self.validation_key != key:
            return False
        if self.key_issued_at + timedelta(days=3) < datetime.now():
            return False
        return True
        
    def has_available_token(self):
        return (self.recipe_token is not None and 
                datetime.now() - timedelta(days=7) < self.token_issued_at)
        
    def issue_recipe_token(self):
        self.recipe_token = str(uuid.uuid4())
        self.token_issued_at = datetime.now()
        
    def add_karma(self, action=None, karma=0):
        if action:
            karma = Karma.actions.get(action)
        self.karma += karma
        threshold = min(10, self.level * 4)
        if (threshold <= self.karma):
            self.level += 1
            self.karma = 0
            point = 1
            self.vote_point += point
            message = u"投票ポイントが%s回分増えました。" % point
            self.user.message_set.create(message=message)
            
    def sub_karma(self, karma=0, action=None):
        if action:
            karma = Karma.actions.get(action)
        self.karma -= karma
            
    def __unicode__(self):
        return self.user.first_name
    
    def delete(self):
        if self.icon:
            self.icon.storage.delete(self.icon.path)
        super(UserProfile, self).delete()

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3


def _create_unique_photo_path(instance, filename, path):
    if instance.photo:
        instance.photo.delete()
        if instance.photo_s3:
            get_taskqueue().send_task(DeleteS3Task({"name":instance.photo_s3.name}),
                                      settings.QUEUENAME_SENDS3)
        instance.photo_s3 = None
        instance.photo_s3_sync = False
        get_taskqueue().send_task(SyncS3Task.from_model(instance), settings.QUEUENAME_SENDS3)
    return os.path.join(path, 
            u"%s%s" % (uuid.uuid4(), os.path.splitext(filename)[1]))

class Recipe(models.Model):
    __metaclass__ = S3SyncModelBase
    
    class Meta:
        verbose_name = verbose_name_plural = u"レシピ"

    objects = managers.RecipeManager()

    name = models.CharField(u"タイトル", 
            max_length=20)
    photo = fields.S3SyncResizedImageField(u"完成写真", 
            upload_to=lambda i, f: _create_unique_photo_path(i, f, u"users/recipe"),
            max_width=500, max_height=500,
            null=True, blank=True)
    introduction = models.TextField(u"紹介文")
    ingredients = models.TextField(u"素材と分量",
                                   editable=False, null=True, blank=True)
    tips = models.TextField(u"作り方のヒント、コツ", 
            null=True, blank=True, default="")
    is_draft = models.BooleanField(u"下書き",
            null=True, blank=True, default=True)
    num_moderated_comments = models.IntegerField(u"承認済みコメント数", 
                                                 editable=False, default=0)
    is_awarded = models.BooleanField(u"優秀レシピ",
            default=False)
    created_at = models.DateTimeField(u"作成日時", 
            auto_now_add=True, 
            editable=False)
    updated_at = models.DateTimeField(u"更新日時", 
            auto_now_add=True, 
            editable=False)
    published_at = models.DateTimeField(u"公開日時", 
            editable=False, null=True, blank=True)
    score = models.IntegerField(u"スコア",
            editable=False, default=0)
    user = models.ForeignKey(User, 
            editable=False, verbose_name=u"投稿者")
    contest = models.ForeignKey(Contest, 
            verbose_name=u"コンテスト",
            editable=False, 
            null=True, blank=True)
    feeling = models.ForeignKey(Feeling, 
            verbose_name=u"フィーリング", 
            null=True, blank=True)
    reviewed_contest = models.ForeignKey(ReviewedContest,
            editable=False, null=True, blank=True,
            verbose_name=u"審査中のお題")
    num_people = models.IntegerField(u"分量の人数", default=2)

    # コピー機能
    parent = models.ForeignKey('self', verbose_name=u'元のレシピ',
            related_name='children', editable=False, null=True, default=None)
    ancestor = models.ForeignKey('self', null=True, editable=False,
            default=None, verbose_name=u'大元のレシピ',
            related_name='descendants')
    retain_originality = models.BooleanField(u'オリジナルから変更あり',
            default=False, editable=False)

    @models.permalink
    def get_absolute_url(self):
        return ("recipes-show", [str(self.id)])
    
    def get_news_text(self):
        return u"%s さんが 「%s」のレシピを書きました。" % (self.user.first_name,
                                            self.name)
    news_text = property(get_news_text)
    
    def get_news_date(self):
        return self.published_at
    news_date = property(get_news_date)
    
    def decode_ingredients(self):
        if self.ingredients:
            return simplejson.loads(self.ingredients)
        else:
            return []

    def decode_ingredients_col(self):
        ings = self.decode_ingredients()
        cutpos = len(ings) / 2
        if len(ings) % 2: cutpos += 1
        return ings[:cutpos], ings[cutpos:]
        
    def ingredient_names(self, num=3):
        ings = self.decode_ingredients()
        return [ ing[0] for ing in ings[:num] ]

    def ingredient_names_str(self, num=3, str_len=25):
        s = " ".join(self.ingredient_names(num))
        if len(s) > str_len:
            s = s[:str_len] + " ..."
        return s
        
    def encode_ingredients(self, names, quantities):
        l = []
        for name, quantity in itertools.izip(names, quantities):
            if name or quantity:
                l.append((name, quantity))
        self.ingredients = simplejson.dumps(l, ensure_ascii=False)

    def __unicode__(self):
        return self.name
    
    def delete(self):
        if self.is_awarded:
            return # 受賞レシピは削除できない
        super(Recipe, self).delete()

    def add_direction(self, direction):
        direction.recipe = self
        direction.number = self.direction_set.count()
            
    def set_request_user(self, user):
        self.is_favorite = self._is_favorite(user)
        self.is_voted = self._is_voted(user)
        
    def _is_favorite(self, user):
        if not user.is_authenticated(): return False
        fav = get_object(FavoriteRecipe, user=user, recipe=self)
        return fav is not None
    
    def _is_voted(self, user):
        if not user.is_authenticated(): return False
        vote = get_object(Vote, user=user, recipe=self)
        return vote is not None
        
    def vote(self, user):
        profile = user.get_profile()
        exists, v = self._vote_or_favorite(Vote, user)
        if not exists:
            self.score += 1
            profile.vote_point -= 1
            if DailyAction.objects.is_done(user, self.user, "vote"):
                # 同じユーザに対して投票済みの場合
                profile.sub_karma(action=Karma.act_vote)
            else:
                DailyScore.objects.add(user, scores.on_vote_to_user)
                profile.add_karma(action=Karma.act_vote)
            profile.save()
        return v
    
    def favorite(self, user):
        exists, fav = self._vote_or_favorite(FavoriteRecipe, user)
        if not exists and not DailyAction.objects.is_done(user, self.user, "favorite"):
            Karma.add_karma(user, Karma.act_favorite)
        return fav
    
    def _vote_or_favorite(self, cls, user):
        try:
            # 同じレシピに対して投票済みの場合
            return True, cls.objects.get(user=user, recipe=self)
        except cls.DoesNotExist, e:
            # なければここで作成
            return False, cls.objects.create(user=user, recipe=self)
    
    def copy(self, user):
        data = {
            'name': self.name,
            'photo': self.photo,
            'introduction': self.introduction,
            'ingredients': self.ingredients,
            'num_people': self.num_people,
            'tips': self.tips,
            'parent': self,
            'ancestor': self.parent or self,
            'retain_originality': True,
            'feeling': self.feeling,
            'user': user,
            'contest': self.contest,
        }
        new_recipe = self.__class__(**data)
        new_recipe.save()
        for direction in self.direction_set.all():
            Direction(
                recipe=new_recipe,
                number=direction.number,
                text=direction.text,
                photo=direction.photo).save()
        return new_recipe

    def moderated_comments(self):
        return Comment.objects.filter(recipe=self).filter(is_moderated=True)
    
    def get_moderated_comments_and_users(self):
        comments = self.moderated_comments()
        users = User.objects.filter(pk__in=comments.values("user_id").query)
        comments = list(comments)
        user_dict = {}
        for user in list(users):
            user_dict[user.id] = user
        users = [ user_dict.get(comment.user_id, None) 
                 for comment in comments ]
        return zip(comments, users)
    
    def toggle_open_state(self):
        self.is_draft = not self.is_draft
        if not self.is_draft and not self.published_at:
            self.published_at = datetime.now()
            user = self.user
            if not DailyAction.objects.is_done(user, user, "create_recipe", time=3):
                Karma.add_karma(user, Karma.act_create_recipe)
                DailyScore.objects.add(user, scores.on_create_recipe_to_user)
                
    def delete_comment(self, comment):
        if comment.is_moderated:
            self.num_moderated_comments -= 1
    
    def ordered_directions(self):
        return self.direction_set.all().order_by("number")
    
    def page_URL(self):
        return '<a href="%s">&raquo;</a>' % reverse("recipes-show", 
                                                 kwargs={"recipe_id":self.id})
    page_URL.allow_tags = True

    def __need_add_index__(self):
        return not self.is_draft
    
    def __need_delete_index__(self):
        return self.is_draft
    
    def __indexdoc__(self):
        if len(feeling_registry) == 0: update_feeling_registry()
        d = {"name":self.name,
             "introduction":self.introduction,
             "ingredients":" ".join([ i[0] for i in self.decode_ingredients()]),
             "tips":self.tips or "",
             "feeling":feeling_registry.get(self.feeling_id, "")}
        return d

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3
    

class Direction(models.Model):
    __metaclass__ = S3SyncModelBase
    
    recipe = models.ForeignKey(Recipe,
            verbose_name=u"レシピ", editable=False)
    number = models.IntegerField(u"順序",
                                 editable=False, default=0)
    text = models.TextField(u"説明")
    photo = fields.S3SyncResizedImageField(u"写真",
            upload_to=lambda i, f: u"users/direction/%s%s" % (uuid.uuid4(), os.path.splitext(f)[1]),
            max_width=150, max_height=150,
            null=True, blank=True)

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3


class Comment(models.Model):
    __metaclass__ = S3SyncModelBase

    objects = managers.CommentManager()
    
    owner = models.ForeignKey(User, verbose_name=u"レシピのユーザ",
                              editable=False, 
                              related_name="owner_comment", 
                              null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=u"ユーザ", 
                             editable=False,
                             related_name="my_comment")
    recipe = models.ForeignKey(Recipe, verbose_name=u"レシピ",
                               editable=False)
    text = models.TextField(u"本文")
    photo = fields.S3SyncResizedImageField(u"写真",
            upload_to=lambda i, f: u"users/comment/%s%s" % (uuid.uuid4(), os.path.splitext(f)[1]),
            max_width=500, max_height=500,
            null=True, blank=True,
            help_text=u"あなたがこのレシピを作った時の写真を載せてください。")
    created_at = models.DateTimeField(auto_now_add=True)
    is_moderated = models.BooleanField(u"承認済み", default=False, 
                                       editable=False)
    
    @models.permalink
    def get_absolute_url(self):
        return ("recipes-show", [str(self.recipe_id)])
    
    def get_news_text(self):
        return u"%s さんが 「%s」のレシピにコメントしました。" % (self.user.first_name,
                                            self.recipe.name)
    news_text = property(get_news_text)
    
    def get_news_date(self):
        return self.created_at
    news_date = property(get_news_date)
    
    def approve(self):
        self.is_moderated = True
        self.recipe.num_moderated_comments += 1
        self.recipe.save()
        user = self.user
        if user != self.owner and \
                not DailyAction.objects.is_done(user, self.owner, "comment"):
            Karma.add_karma(user, Karma.act_comment)
            DailyScore.objects.add(user, scores.on_comment_to_user)

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3

    
class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, verbose_name=u"ユーザ", editable=False)
    recipe = models.ForeignKey(Recipe) # 自分のレシピを除く
    created_at = models.DateTimeField(auto_now_add=True)


class FavoriteUser(models.Model):
    objects = managers.FavoriteUserManager()
    
    user = models.ForeignKey(User, verbose_name=u"ユーザ", editable=False,
                             related_name="owner")
    target = models.ForeignKey(User, verbose_name=u"対象ユーザ", editable=False,
                               related_name="target")
    created_at = models.DateTimeField(auto_now_add=True)
    
    
class Vote(models.Model):
    user = models.ForeignKey(User, verbose_name=u"ユーザ", editable=False)
    recipe = models.ForeignKey(Recipe, verbose_name=u"レシピ")
    created_at = models.DateTimeField(auto_now_add=True)
    

feeling_registry = {}
def update_feeling_registry():
    feeling_registry.clear()
    [ feeling_registry.setdefault(feeling.pk, feeling.name)
        for feeling in Feeling.objects.all() ]

dish_registry = {}
def update_dish_registry():
    dish_registry.clear()
    [ dish_registry.setdefault(dish.pk, dish.name) 
        for dish in Dish.objects.all() ]

register_task(UserProfile)
register_task(Recipe)
register_task(Direction)
register_task(Comment)

register_index(Contest)
register_index(Recipe)
