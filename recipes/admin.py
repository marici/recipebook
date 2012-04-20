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
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
import models


class IngredientCategoryAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.IngredientCategory, IngredientCategoryAdmin)


class IngredientAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Ingredient, IngredientAdmin)


class DishCategoryAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.DishCategory, DishCategoryAdmin)


class DishAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Dish, DishAdmin)


class FeelingAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.Feeling, FeelingAdmin)


class FarmProducerAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.FarmProducer, FarmProducerAdmin)


class ContestAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'dish', 'feeling', 'ingredients', 'description',
                      'image', 'producer', 'published_at', 'closed_at',
                      'finished_at')
        }),
        (u'審査', {
            'classes': ('collapse',),
            'fields': ('is_reviewing', 'is_finished', 'comment',
                      'reviewing_photo1', 'reviewing_photo2',
                      'reviewing_photo3', 'reviewing_photo4',
                      'reviewing_photo5', ),
            'description': u'以下の項目は締め切り日を過ぎていなければ変更できません。'
        }),
    )
    list_display = ('name', 'created_at', 'published_at', 'closed_at',
                    'finished_at', 'is_reviewing', 'is_finished')
    date_hierarchy = 'published_at'

    def save_model(self, request, obj, form, change):
        self.validate_flags(obj)
        if change:
            if obj.is_reviewing:
                try:
                    status = models.ReviewedContest.objects.get(contest=obj.id)
                except ObjectDoesNotExist:
                    self.start_reviewing_mode(obj)
                else:
                    status.name = obj.name
                    status.save()
            else:
                self.stop_reviewing_mode(obj)
            if obj.is_finished and obj.is_reviewing:
                obj.is_reviewing = False
                self.stop_reviewing_mode(obj)
        obj.save()

    def validate_flags(self, obj):
        if datetime.now() < obj.closed_at:
            obj.is_reviewing = False
            obj.is_finished = False
            obj.comment = None

    def start_reviewing_mode(self, obj):
        status = models.ReviewedContest.objects.create(contest=obj,
                name=obj.name)
        models.Recipe.objects.filter(contest=obj.id)\
                .update(reviewed_contest=status)

    def stop_reviewing_mode(self, obj):
        try:
            status = models.ReviewedContest.objects.get(contest=obj.id)
            models.Recipe.objects.filter(reviewed_contest=status.id)\
                    .update(reviewed_contest=None)
            status.delete()
        except ObjectDoesNotExist:
            pass

admin.site.register(models.Contest, ContestAdmin)


class ReviewedContestAdmin(admin.ModelAdmin):
    pass
admin.site.register(models.ReviewedContest, ReviewedContestAdmin)


class RecipeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('is_awarded',)
        }),
    )
    list_display = ('name', 'user', 'introduction', 'contest', 'created_at',
                    'score', 'is_awarded', 'page_URL')
    list_filter = ('reviewed_contest', 'created_at')

admin.site.register(models.Recipe, RecipeAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_female', 'birth_year', 'prefecture',
                    'validation_key')
admin.site.register(models.UserProfile, UserProfileAdmin)
