# -*- coding: utf-8 -*-
from .master import *


# =======================================================
# 運営しながら作成するデータ
# =======================================================

class FarmProducer(models.Model):
    '''
    食材生産者
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'食材生産者'

    name = models.CharField(u'名前', max_length=50)
    introduction = models.TextField(u'紹介文')
    photo = models.ImageField(u'写真',
                              upload_to=u'public/producer',
                              null=True, blank=True)
    url = models.URLField(u'URL', null=True, blank=True)

    def __unicode__(self):
        return self.name


class Contest(models.Model):
    '''
    募集するお題
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'お題'

    class NotAllowedShow(Exception): pass
    class NotAllowedSubmit(Exception): pass

    objects = managers.ContestManager()

    name = models.CharField(max_length=50,
            verbose_name=u'タイトル')
    ingredients = models.ManyToManyField(Ingredient,
            verbose_name=u'食材',
            null=True, blank=True)
    dish = models.ForeignKey(Dish,
            verbose_name=u'料理',
            null=True, blank=True)
    feeling = models.ForeignKey(Feeling,
            verbose_name=u'フィーリング',
            null=True, blank=True)
    description = models.TextField(u'説明')
    image = fields.ResizedImageField(u'イメージ',
            max_width=500, max_height=500,
            upload_to=u'public/contest/',
            null=True, blank=True)
    producer = models.ForeignKey(FarmProducer,
                                 verbose_name=u'生産者',
                                 null=True, blank=True)
    royalty = models.PositiveSmallIntegerField(u'ロイヤルティ率',
                                               default=3)
    created_at = models.DateTimeField(u'作成日',
            auto_now_add=True)
    published_at = models.DateTimeField(u'募集開始日')
    closed_at = models.DateTimeField(u'募集締切日')
    finished_at = models.DateTimeField(u'審査結果発表日')
    is_reviewing = models.BooleanField(u'審査中', default=False)
    is_finished = models.BooleanField(u'審査完了', default=False)
    comment = models.TextField(u'選評', null=True, blank=True)
    rp_kwargs = {'upload_to': 'public/contest/review', 'null': True,
            'blank': True, 'max_width': 300, 'max_height': 300}
    reviewing_photo1 = fields.ResizedImageField(u'審査写真1', **rp_kwargs)
    reviewing_photo2 = fields.ResizedImageField(u'審査写真2', **rp_kwargs)
    reviewing_photo3 = fields.ResizedImageField(u'審査写真3', **rp_kwargs)
    reviewing_photo4 = fields.ResizedImageField(u'審査写真4', **rp_kwargs)
    reviewing_photo5 = fields.ResizedImageField(u'審査写真5', **rp_kwargs)

    def __unicode__(self):
        return self.name

    def pre_view(self, user, ctxd={}, extra=None):
        if not self.is_published():
            raise self.NotAllowedShow()
        ctxd['contests'] = Contest.objects.get_current_contests()
        if self.is_really_finished():
            award_recipes = self.get_awarded_recipes()
            ctxd['top_award_recipes'] = award_recipes[:2]
            ctxd['award_recipes'] = award_recipes[2:]

    @models.permalink
    def get_absolute_url(self):
        return ('recipes-contests-show', [str(self.id)])

    def pre_submit_recipe(self, user, recipe):
        if recipe.user != user or recipe.contest:
            raise self.NotAllowedSubmit()

    def post_submit_recipe(self, user, recipe):
        pass

    def is_published(self):
        return self.published_at <= datetime.now()

    def is_closed(self, now=None):
        now = now or datetime.now()
        return self.closed_at <= now

    def is_really_finished(self):
        now = datetime.now()
        return (self.is_finished and self.finished_at and
                self.finished_at <= now)

    def get_left_days(self):
        return (self.closed_at - datetime.now()).days
    left_days = property(get_left_days)

    def open_recipes(self):
        return self.recipe_set.filter(is_draft=False)

    def get_new_recipes(self, number=10):
        qs = self.recipe_set.filter(is_draft=False).order_by('-created_at')
        return list(qs[: number])

    def get_featured_recipes(self, number=3):
        qs = self.recipe_set.filter(is_draft=False)\
                .filter(score__lt=10).order_by('-score')
        return list(qs[: number])
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
        d = {'name': self.name,
             'description': self.description,
             'dish': dish_registry.get(self.dish_id, ''),
             'feeling': feeling_registry.get(self.feeling_id, ''),
             'ingredients': ' '.join(
                 [ing.name for ing in self.ingredients.all()])
        }
        return d

    def to_dict(self):
        return {
            'name':  self.name,
            'id': self.id,
            'dish': self.dish.name if self.dish else None,
            'image': self.image.url if self.image else None,
            'description': self.description,
            'feeling': self.feeling.name if self.feeling else None,
        }


class ReviewedContest(models.Model):
    '''
    審査中のお題
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'審査中のお題'

    contest = models.ForeignKey(Contest, verbose_name=u'お題',
                                null=True, blank=True)
    name = models.CharField(u'タイトル', max_length=20)

    def __unicode__(self):
        return self.name
