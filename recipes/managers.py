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
from datetime import datetime
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from recipebook.maricilib.django.apps.search import searcher
import models as recipe_models

ingredients = None

def fill_ingredients():
    global ingredients
    if ingredients is not None: return
    ingredients = {}
    for ing in recipe_models.Ingredient.objects.all():
        ingredients[ing.name] = ing


class ContestManager(models.Manager):
    """
    contestテーブルに対する操作の実装クラス。
    """
    def search(self, queries, fields=None, page=1, per_page=10):
        fill_ingredients()
        # 食材に一致すれば関連から取得
        if len(queries) == 1 and queries[0] in ingredients:
            contests = ingredients.get(queries[0]).contest_set.all()
            return {"hits":contests.count(), "object_list":contests}
        else:
            if searcher is None:
                contests = self.filter(published_at__lte=datetime.now()) \
                    .filter(description__icontains=queries[0])
                return {"hits":contests.count(), "object_list":contests}
            else:
                return searcher.search(self, queries, fields, page, per_page)
        
    def get_current_contests(self):
        now = datetime.now()
        return self.filter(published_at__lte=now).filter(closed_at__gt=now)

    def get_closed_contests_qs(self):
        now = datetime.now()
        return self.filter(closed_at__lte=now)


class RecipeManager(models.Manager):
    """
    recipeテーブルに対する操作の実装クラス。
    """
    def search(self, queries, fields=None, page=1, per_page=10):
        if searcher is None:
            return {"hits":0, "object_list":[]}
        else:
            return searcher.search(self, queries, fields, page, per_page)

    def get_popular_recipes(self, user):
        recipes = list(self.filter(user=user).filter(is_awarded=True))
        for recipe in self.filter(user=user) \
                            .filter(is_draft=False) \
                            .exclude(score=0) \
                            .order_by("-score"):
            if recipe not in recipes: recipes.append(recipe)
        return recipes
    
    def get_recent_recipes(self, user, allow_draft=False):
        qs = self.filter(user=user)
        if allow_draft:
            qs = qs.order_by("-created_at")
        else:
            qs = qs.filter(is_draft=False).order_by("-published_at")
        return qs
    
    def get_favorite_user_recipes(self, user):
        fav_members_qs = recipe_models.FavoriteUser.objects.filter(
            user=user).values("pk").query
        qs = self.filter(user__in=fav_members_qs).order_by("-published_at")
        return qs
        
    def favorite_recipes(self, user):
        fav_recipe_ids = recipe_models.FavoriteRecipe.objects.filter(
            user=user).values("recipe_id").query
        return self.filter(pk__in=fav_recipe_ids).order_by("-published_at")
    

class CommentManager(models.Manager):
    
    def get_owner_comments(self, user):
        return self.filter(owner=user).exclude(user=user).order_by("-created_at")
    

class FavoriteUserManager(models.Manager):
    
    limit = 20
    
    def reach_limit(self, user):
        return (self.limit <= self.filter(user=user).count())
     
    def get_favorite_users(self, user):
        fav_users_qs = self.filter(user=user).values("target").query
        return User.objects.filter(pk__in=fav_users_qs)

    def get_favorite_user_actions(self, user):
        fav_user_ids = self.filter(user=user).values("target").query
        recipes = recipe_models.Recipe.objects.filter(user__in=fav_user_ids)\
                                .filter(is_draft=False)\
                                .order_by("-published_at")
        comments = recipe_models.Comment.objects.filter(user__in=fav_user_ids)\
                                  .filter(is_moderated=True)\
                                  .order_by("-created_at")
        actions = list(recipes) + list(comments)
        def time_for_cmp(x):
            if x.__class__ == recipe_models.Recipe:
                return x.published_at or x.created_at
            else:
                return x.created_at
        actions.sort(lambda x, y: cmp(time_for_cmp(x), time_for_cmp(y)))
        actions.reverse()
        return actions
    
    def favorite_user_recipes(self, user):
        pass
        
class UserProfileManager(models.Manager):
    
    def create_pending_user(self, user, **kwargs):
        profile = self.model(user=user, **kwargs)
        profile.generate_validation_key()
        profile.save()
        return profile
        
    def active_beginners(self, start, limit=10):
        qs = self.filter(created_at__gt=start).order_by("-level")[:limit]
        user_ids = [ profile.user_id for profile in list(qs) ]
        return User.objects.filter(pk__in=user_ids).filter(is_active=True)

    def get_zipped_profiles(self, users, user_ids):
        profiles = self.filter(user__in=user_ids)
        d = {}
        for profile in list(profiles):
            d[profile.user_id] = profile
        return [ {"user":user,"profile":d.get(user.id, None)} 
                for user in users ]
