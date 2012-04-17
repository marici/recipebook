# -*- coding: utf-8 -*-
from .service import *


# =======================================================
# ユーザが作成するデータ
# =======================================================

class UserProfile(models.Model):
    __metaclass__ = S3SyncModelBase

    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'メンバープロファイル'

    objects = managers.UserProfileManager()

    user = models.ForeignKey(User, verbose_name=u'メンバー', unique=True,
                             editable=False)
    validation_key = models.CharField(u'バリデーションキー', max_length=50,
                                      null=True, blank=True, db_index=True,
                                      editable=False)
    key_issued_at = models.DateTimeField(u'キー発行日時', null=True, blank=True,
                                         editable=False)
    recipe_token = models.CharField(u'投稿トークン', max_length=50,
                                    null=True, blank=True, editable=False)
    token_issued_at = models.DateTimeField(u'トークン発行日時', null=True, blank=True,
                                           editable=False)
    pending_email = models.EmailField(u'変更メールアドレス', null=True, blank=True,
                                    editable=False)
    alter_email = models.EmailField(u'代替メールアドレス', null=True, blank=True,
                                    editable=False)
    is_female = models.BooleanField(u'性別 (女性)', default=True)
    birth_year = models.PositiveIntegerField(u'生年', null=True, blank=True)
    prefecture = models.CharField(u'住所 (県)', max_length=50,
                                  null=True, blank=True)
    profile_text = models.TextField(u'プロフィール', null=True, blank=True)
    blog_url = models.URLField(u'ブログURL', null=True, blank=True)
    icon = fields.S3SyncResizedImageField(u'アイコン',
                             upload_to=lambda i, f: i.make_icon_filepath(f),
                             max_width=100, max_height=100,
                             null=True, blank=True)
    deny_comment = models.BooleanField(u'コメント拒否', default=False)
    deny_mail_magazine = models.BooleanField(u'お知らせメール拒否', default=False)
    karma = models.IntegerField(u'カルマ', editable=False, default=0)
    level = models.IntegerField(u'レベル', editable=False, default=1)
    vote_point = models.PositiveIntegerField(u'投票ポイント', editable=False,
                                             default=1)
    created_at = models.DateTimeField(u'作成日', auto_now_add=True)

    def make_icon_filepath(self, filename):
        ext = os.path.splitext(filename)[1]
        path = 'users/icon/%s%s' % (self.user.id, ext)
        self.icon.storage.delete(path)
        if self.icon_s3:
            get_taskqueue().send_task(DeleteS3Task({'name': path}),
                                      settings.QUEUENAME_SENDS3)
        self.icon_s3 = None
        self.icon_s3_sync = False
        get_taskqueue().send_task(SyncS3Task.from_model(self),
                settings.QUEUENAME_SENDS3)
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
            get_taskqueue().send_task(
                    DeleteS3Task({'name': instance.photo_s3.name}),
                    settings.QUEUENAME_SENDS3)
        instance.photo_s3 = None
        instance.photo_s3_sync = False
        get_taskqueue().send_task(SyncS3Task.from_model(instance),
                settings.QUEUENAME_SENDS3)
    return os.path.join(path,
            u'%s%s' % (uuid.uuid4(), os.path.splitext(filename)[1]))


class Recipe(models.Model):
    __metaclass__ = S3SyncModelBase

    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'レシピ'

    objects = managers.RecipeManager()

    name = models.CharField(u'タイトル',
            max_length=20)
    photo = fields.S3SyncResizedImageField(u'完成写真',
            upload_to=lambda i, f: _create_unique_photo_path(
                i, f, u'users/recipe'),
            max_width=500, max_height=500,
            null=True, blank=True)
    introduction = models.TextField(u'紹介文')
    ingredients = models.TextField(u'素材と分量',
                                   editable=False, null=True, blank=True)
    tips = models.TextField(u'作り方のヒント、コツ',
            null=True, blank=True, default='')
    is_draft = models.NullBooleanField(u'下書き',
            null=True, blank=True, default=True)
    num_moderated_comments = models.IntegerField(u'承認済みコメント数',
                                                 editable=False, default=0)
    is_awarded = models.BooleanField(u'優秀レシピ',
            default=False)
    created_at = models.DateTimeField(u'作成日時',
            auto_now_add=True,
            editable=False)
    updated_at = models.DateTimeField(u'更新日時',
            auto_now_add=True,
            editable=False)
    published_at = models.DateTimeField(u'公開日時',
            editable=False, null=True, blank=True)
    score = models.IntegerField(u'スコア',
            editable=False, default=0)
    user = models.ForeignKey(User,
            editable=False, verbose_name=u'投稿者')
    contest = models.ForeignKey(Contest,
            verbose_name=u'コンテスト',
            editable=False,
            null=True, blank=True)
    feeling = models.ForeignKey(Feeling,
            verbose_name=u'フィーリング',
            null=True, blank=True)
    reviewed_contest = models.ForeignKey(ReviewedContest,
            editable=False, null=True, blank=True,
            verbose_name=u'審査中のお題')
    num_people = models.IntegerField(u'分量の人数', default=2)

    # コピー機能
    parent = models.ForeignKey('self', verbose_name=u'元のレシピ',
            related_name='children', editable=False, null=True, default=None)
    ancestor = models.ForeignKey('self', null=True, editable=False,
            default=None, verbose_name=u'大元のレシピ',
            related_name='descendants')

    def open_children(self):
        return self.children.filter(is_draft=False)

    @models.permalink
    def get_absolute_url(self):
        return ('recipes-show', [str(self.id)])

    def get_news_text(self):
        return u'%s さんが 「%s」のレシピを書きました。' % (self.user.first_name,
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
        return [ing[0] for ing in ings[:num]]

    def ingredient_names_str(self, num=3, str_len=25):
        s = ' '.join(self.ingredient_names(num))
        if len(s) > str_len:
            s = s[: str_len] + ' ...'
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
            return  # 受賞レシピは削除できない
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
            if DailyAction.objects.is_done(user, self.user, 'vote'):
                # 同じユーザに対して投票済みの場合
                profile.sub_karma(action=Karma.act_vote)
            else:
                DailyScore.objects.add(user, scores.on_vote_to_user)
                profile.add_karma(action=Karma.act_vote)
            profile.save()
        return v

    def favorite(self, user):
        exists, fav = self._vote_or_favorite(FavoriteRecipe, user)
        if not exists and not DailyAction.objects.is_done(
                user, self.user, 'favorite'):
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
            'name': u'%s のアレンジ' % self.name,
            'photo': self.photo,
            'introduction': u'＜アレンジレシピの紹介文＞',
            'ingredients': self.ingredients,
            'num_people': self.num_people,
            'tips': self.tips,
            'parent': self,
            'ancestor': self.parent or self,
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
        users = User.objects.filter(pk__in=comments.values('user_id').query)
        comments = list(comments)
        user_dict = {}
        for user in list(users):
            user_dict[user.id] = user
        users = [user_dict.get(comment.user_id, None)
                 for comment in comments]
        return zip(comments, users)

    def toggle_open_state(self):
        self.is_draft = not self.is_draft
        if not self.is_draft and not self.published_at:
            self.published_at = datetime.now()
            user = self.user
            if not DailyAction.objects.is_done(user, user, 'create_recipe',
                    time=3):
                Karma.add_karma(user, Karma.act_create_recipe)
                DailyScore.objects.add(user, scores.on_create_recipe_to_user)

    def delete_comment(self, comment):
        if comment.is_moderated:
            self.num_moderated_comments -= 1

    def ordered_directions(self):
        return self.direction_set.all().order_by('number')

    def page_URL(self):
        return '<a href="%s">&raquo;</a>' % reverse('recipes-show',
                                                 kwargs={'recipe_id': self.id})
    page_URL.allow_tags = True

    def __need_add_index__(self):
        return not self.is_draft

    def __need_delete_index__(self):
        return self.is_draft

    def __indexdoc__(self):
        if len(feeling_registry) == 0: update_feeling_registry()
        d = {'name': self.name,
             'introduction': self.introduction,
             'ingredients': ' '.join(
                 [i[0] for i in self.decode_ingredients()]),
             'tips': self.tips or '',
             'feeling': feeling_registry.get(self.feeling_id, '')}
        return d

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3


class Direction(models.Model):
    __metaclass__ = S3SyncModelBase

    class Meta:
        app_label = 'recipes'

    recipe = models.ForeignKey(Recipe,
            verbose_name=u'レシピ', editable=False)
    number = models.IntegerField(u'順序',
                                 editable=False, default=0)
    text = models.TextField(u'説明')
    photo = fields.S3SyncResizedImageField(u'写真',
            upload_to=lambda i, f: u'users/direction/%s%s' % (uuid.uuid4(),
                os.path.splitext(f)[1]),
            max_width=150, max_height=150,
            null=True, blank=True)

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3


class Comment(models.Model):
    __metaclass__ = S3SyncModelBase

    class Meta:
        app_label = 'recipes'

    objects = managers.CommentManager()

    owner = models.ForeignKey(User, verbose_name=u'レシピのユーザ',
                              editable=False,
                              related_name='owner_comment',
                              null=True, blank=True)
    user = models.ForeignKey(User, verbose_name=u'ユーザ',
                             editable=False,
                             related_name='my_comment')
    recipe = models.ForeignKey(Recipe, verbose_name=u'レシピ',
                               editable=False)
    text = models.TextField(u'本文')
    photo = fields.S3SyncResizedImageField(u'写真',
            upload_to=lambda i, f: u'users/comment/%s%s' % (
                uuid.uuid4(), os.path.splitext(f)[1]),
            max_width=500, max_height=500,
            null=True, blank=True,
            help_text=u'あなたがこのレシピを作った時の写真を載せてください。')
    created_at = models.DateTimeField(auto_now_add=True)
    is_moderated = models.BooleanField(u'承認済み', default=False,
                                       editable=False)

    @models.permalink
    def get_absolute_url(self):
        return ('recipes-show', [str(self.recipe_id)])

    def get_news_text(self):
        return u'%s さんが 「%s」のレシピにコメントしました。' % (self.user.first_name,
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
                not DailyAction.objects.is_done(user, self.owner, 'comment'):
            Karma.add_karma(user, Karma.act_comment)
            DailyScore.objects.add(user, scores.on_comment_to_user)

    def __post_save_task__(self):
        return SyncS3Task.from_model(self), settings.QUEUENAME_SENDS3


class FavoriteRecipe(models.Model):
    class Meta:
        app_label = 'recipes'

    user = models.ForeignKey(User, verbose_name=u'ユーザ', editable=False)
    recipe = models.ForeignKey(Recipe)  # 自分のレシピを除く
    created_at = models.DateTimeField(auto_now_add=True)


class FavoriteUser(models.Model):
    class Meta:
        app_label = 'recipes'

    objects = managers.FavoriteUserManager()

    user = models.ForeignKey(User, verbose_name=u'ユーザ', editable=False,
                             related_name='owner')
    target = models.ForeignKey(User, verbose_name=u'対象ユーザ', editable=False,
                               related_name='target')
    created_at = models.DateTimeField(auto_now_add=True)


class Vote(models.Model):
    class Meta:
        app_label = 'recipes'

    user = models.ForeignKey(User, verbose_name=u'ユーザ', editable=False)
    recipe = models.ForeignKey(Recipe, verbose_name=u'レシピ')
    created_at = models.DateTimeField(auto_now_add=True)
