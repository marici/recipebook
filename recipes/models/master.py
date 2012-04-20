# -*- coding: utf-8 -*-
from base import *


# =======================================================
# マスタデータ
# =======================================================

class IngredientCategory(models.Model):
    '''
    野菜、夏の食べ物などの食材カテゴリ
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'食材カテゴリ'

    name = models.CharField(max_length=20)
    photo = models.ImageField(u'写真',
                              upload_to=u'public/ingcategory',
                              null=True, blank=True)

    def __unicode__(self):
        return self.name


class Ingredient(models.Model):
    '''
    茄子、豚肉などの代表的な食材
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'食材'

    name = models.CharField(max_length=20)
    photo = models.ImageField(u'写真',
                              upload_to=u'public/ingredient',
                              null=True, blank=True)
    categories = models.ManyToManyField('IngredientCategory')

    def __unicode__(self):
        return self.name


class DishCategory(models.Model):
    '''
    肉料理、煮物などの料理カテゴリ
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'料理カテゴリ'

    name = models.CharField(max_length=20)
    photo = models.ImageField(u'写真',
                              upload_to=u'public/dishcategory',
                              null=True, blank=True)

    def __unicode__(self):
        return self.name


class Dish(models.Model):
    '''
    ハンバーグ、クリームシチューなどの代表的な料理
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'料理'

    name = models.CharField(max_length=20)
    photo = models.ImageField(u'写真',
                              upload_to=u'public/dish',
                              null=True, blank=True)
    categories = models.ManyToManyField('DishCategory')

    def save(self, force_insert=False, force_update=False):
        dish_registry.clear()
        super(Dish, self).save(force_insert, force_update)

    def __unicode__(self):
        return self.name


class Feeling(models.Model):
    '''
    「子供が喜ぶ」「ヘルシー」などの代表的なフィーリング
    '''
    class Meta:
        app_label = 'recipes'
        verbose_name = verbose_name_plural = u'フィーリング'

    name = models.CharField(max_length=20)
    photo = models.ImageField(u'写真',
                              upload_to=u'public/feeling',
                              null=True, blank=True)

    def save(self, force_insert=False, force_update=False):
        feeling_registry.clear()
        super(Feeling, self).save(force_insert, force_update)

    def __unicode__(self):
        return self.name


feeling_registry = {}
dish_registry = {}


def update_feeling_registry():
    feeling_registry.clear()
    [feeling_registry.setdefault(feeling.pk, feeling.name)
        for feeling in Feeling.objects.all()]


def update_dish_registry():
    dish_registry.clear()
    [dish_registry.setdefault(dish.pk, dish.name)
        for dish in Dish.objects.all()]
