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
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from models import *
from recipes import forms

user1 = {"username":"testuser1_at_marici_co_jp", "password":"password"}
user2 = {"username":"testuser2_at_marici_co_jp", "password":"password"}
user3 = {"username":"testuser3_at_marici_co_jp", "password":"password"}

class RecipesViewsTest(TestCase):
    """
    recipes.views.__init__.pyに対する機能テスト。
    """

    fixtures = ["test_recipes.json", "test_auth.json"]

    def setUp(self):
        pass

    def test_show_recipe(self):
        """
        url: recipes-show
        指定したIDのレシピが返される。
        """
        recipe_id = 1
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.failUnlessEqual(response.status_code, 200)
        recipe = response.context[0]["recipe"]
        self.assertEquals(recipe_id, recipe.id)

    def test_show_draft_recipe(self):
        """
        url: recipes-show
        レシピがドラフトの場合、403レスポンスが返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.is_draft = True
        recipe.save()

        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.failUnlessEqual(response.status_code, 403)

    def test_show_draft_recipe_to_creator(self):
        """
        url: recipes-show
        レシピがドラフトでユーザが作成者の場合、指定したIDのレシピが返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.is_draft = True
        recipe.save()

        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.failUnlessEqual(response.status_code, 200)
        recipe = response.context[0]["recipe"]
        self.assertEquals(recipe_id, recipe.id)

    def test_show_nonexistence_recipe(self):
        """
        url: recipes-show
        レシピが存在しない場合、404が返される
        """
        recipe_id = 10000
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_recipe_submitted(self):
        """
        url:recipes-show
        お題に提出済みで公開したことがある場合、編集リンクは表示されない。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.published_at = datetime.now()
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        self.client.login(**user1)
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        edit_path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertNotContains(response, edit_path, 200)

    def test_show_recipe_submitted_draft(self):
        """
        url:recipes-show
        お題にひもづいているが公開したことがない場合、編集リンクは表示される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.published_at = None
        recipe.is_draft = True
        recipe.is_awarded = False
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        self.client.login(**user1)
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        edit_path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertContains(response, edit_path, status_code=200)

    def test_show_recipe_awarded(self):
        """
        url:recipes-show
        受賞レシピの場合、編集リンク、削除リンクは表示されない。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        self.client.login(**user1)
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        edit_path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertNotContains(response, edit_path, 200)
        delete_path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertNotContains(response, delete_path, 200)

    def test_show_recipe_nonactive_user(self):
        """
        url:recipes-show
        ユーザがアクティブでなければ404を返す。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        u1 = User.objects.get(username=user1.get("username"))
        u1.is_active = False
        u1.save()
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_recipe_nonactive_user_awarded(self):
        """
        url:recipes-show
        ユーザがアクティブでなくても受賞レシピであれば200を返す。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        u1 = User.objects.get(username=user1.get("username"))
        u1.is_active = False
        u1.save()
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_show_recipe_awarded(self):
        """
        url:recipes-show
        受賞していて、結果が発表されていればマークを表示
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now()
        contest.finished_at = datetime.now()
        contest.is_finished = True
        contest.save()
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon_awardedstatus.jpg")
        
    def test_show_recipe_awarded_unfinished(self):
        """
        url:recipes-show
        受賞していて、結果が発表されていなけばマークを表示しない
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now() + timedelta(days=1)
        contest.finished_at = datetime.now() + timedelta(days=1)
        contest.is_finished = True
        contest.save()
        path = reverse("recipes-show", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "icon_itemstatus03.jpg")
        
    def test_show_recipe_for_print_nonactive_user(self):
        """
        url:recipes-show-print
        ユーザがアクティブでなければ404を返す。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        u1 = User.objects.get(username=user1.get("username"))
        u1.is_active = False
        u1.save()
        path = reverse("recipes-show-print", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_recipe_for_print_nonactive_user_awarded(self):
        """
        url:recipes-show-print
        ユーザがアクティブでなくても受賞していれば200を返す。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        u1 = User.objects.get(username=user1.get("username"))
        u1.is_active = False
        u1.save()
        path = reverse("recipes-show-print", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_register_recipe_get_nologin(self):
        """
        url: recipes-register(GET)
        ログインしていない場合、302が返される。
        """
        path = reverse("recipes-register", kwargs={})
        response = self.client.get(path)
        self.assertRedirects(response,"/accounts/login/?next=/recipe/register/", 302, 200)

    def test_register_recipe_get_login(self):
        """
        url: recipes-register(GET)
        ログインしている場合、200が返される。
        """
        path = reverse("recipes-register")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)

    def test_register_recipe_post_nologin(self):
        """
        url: recipes-register(POST)
        ログインしていない場合、302が返される。
        """
        path = reverse("recipes-register")
        response = self.client.post(path)
        self.assertRedirects(response,"/accounts/login/?next=/recipe/register/", 302, 200)

    def test_register_recipe_post_login_incomplete(self):
        """
        url: recipes-register(POST)
        フィールドの要素が不足している場合、403が返される。
        """
        path = reverse("recipes-register")
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertFormError(response,"form","name","This field is required.")
        self.assertFormError(response, "form", "introduction", "This field is required.")
        self.assertEqual(response.status_code, 200)

    def test_register_recipe_post_login(self):
        """
        url:recipes-register(POST)
        新しいレシピの作成に成功した場合、編集ページへリダイレクトされ200を返される。
        このときレシピはドラフトとなる。
        """
        post_data = {
            "name": "Test New Recipe Name",
            "introduction": "Test New Recipe Introduction."
        }
        path = reverse("recipes-register")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        recipe = Recipe.objects.get(name="Test New Recipe Name")
        edit_page_url = reverse("recipes-edit", kwargs={"recipe_id":recipe.id})
        self.assertRedirects(response, edit_page_url, 302, 200)
        self.assertTrue(recipe.is_draft)

    def test_toggle_recipe_open_state_nologin(self):
        """
        url:recipes-change-status
        ログインしていない場合、ログインページへリダイレクトる。
        """
        recipe_id = 1
        path = reverse("recipes-change-status", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_toggle_recipe_open_state_login_another_user(self):
        """
        url:recipes-change-status
        ログイン者と対象のレシピの作成者が違う場合、403が返される。
        """
        recipe_id = 1
        path = reverse("recipes-change-status", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 403)

    def test_toggle_recipe_open_state_nonexistence_recipe(self):
        """
        url:recipes-change-status
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-change-status", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)

    def test_toggle_recipe_open_state_login(self):
        """
        url:recipes-change-status
        ログイン済みでレシピの作成者であれば302が返され、編集ページにリダイレクトされる。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        path = reverse("recipes-change-status", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(recipe.user.username, user1["username"])
        edit_page_url = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertEquals(response.status_code, 200)

    def test_toggle_recipe_open_state_awarded(self):
        """
        url:recipes-change-status
        受賞レシピは非公開にすることができない。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.is_awarded = True
        recipe.save()
        path = reverse("recipes-change-status", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(recipe.user.username, user1["username"])
        edit_page_url = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_get_nologin(self):
        """
        url:recipes-edit
        ログインしていない場合、ログインページへリダイレクトる。
        """
        recipe_id = 1
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        response = self.client.get(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_edit_recipe_get_login_another_user(self):
        """
        url:recipes-edit
        ログイン者と対象のレシピの作成者が違う場合、403が返される。
        """
        recipe_id = 1
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.get(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_get_nonexistence_recipe(self):
        """
        url:recipes-edit
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 404)

    def test_edit_recipe_get_login(self):
        """
        url:recipes-edit
        ログイン済みでレシピの作成者であれば200が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)

    def test_edit_recipe_get_submitted(self):
        """
        url:recipes-edit
        一度でも公開したことがあり、お題に提出済みの場合、403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.published_at = datetime.now()
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_get_submitted_draft(self):
        """
        url:recipes-edit
        お題にひもづいているが公開したことがない場合、200が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.published = None
        recipe.is_draft = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 200)

    def test_edit_recipe_get_awarded(self):
        """
        url:recipes-edit
        受賞レシピの場合、403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_post_nologin(self):
        """
        url:recipes-edit
        ログインしていない場合、ログインページへリダイレクトされる。
        """
        recipe_id = 1
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_edit_recipe_post_login_another_user(self):
        """
        url:recipes-edit
        ログイン者と対象のレシピの作成者が違う場合、403が返される。
        """
        recipe_id = 1
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_post_nonexistence_recipe(self):
        """
        url:recipes-edit
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)

    def test_edit_recipe_post_login(self):
        """
        url:recipes-edit
        ログイン済みでレシピの作成者であれば302が返され、編集ページへリダイレクトされる。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertRedirects(response, path, 302, 200)

    def test_edit_recipe_post_submitted(self):
        """
        url:recipes-edit
        お題に提出済みの場合、403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.published_at = datetime.now()
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)

    def test_edit_recipe_post_submitted_draft(self):
        """
        url:recipes-edit
        お題にひもづいているが、一度も公開していない場合、編集ができる。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_draft = True
        recipe.published_at = None
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertRedirects(response, path, 302, 200)

    def test_edit_recipe_post_awarded(self):
        """
        url:recipes-edit
        受賞レシピの場合、403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-edit", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)

    def test_delete_recipe_post_submitted(self):
        """
        url:recipes-delete
        お題に提出済みの場合、削除はできる。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-delete", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertRedirects(response, "/home/", 302, 200)
        try:
            Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist, e:
            pass
        else:
            self.fail("The recipe should be deleted.")

    def test_delete_recipe_post_awarded(self):
        """
        url:recipes-delete
        受賞レシピの場合、403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-delete", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)
        try:
            Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist, e:
            self.fail("The recipe shouldn't be deleted.")
        else:
            pass

    def test_register_direction_nologin(self):
        """
        url: recipes-direction-register
        ログインしていない場合はログインページへリダイレクトされ、302が返される。
        """
        recipe_id = 1
        path = reverse("recipes-direction-register", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_register_direction_login_another_user(self):
        """
        url:recipes-direction-register
        ログイン者と対象のレシピの作成者が違う場合、403が返される。
        """
        recipe_id = 1
        path = reverse("recipes-direction-register", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 403)

    def test_register_direction_nonexistence_recipe(self):
        """
        url:recipes-direction-register
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-direction-register", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)

    def test_register_direction_login(self):
        """
        url:recipes-direction-register
        ログイン済みでレシピの作成者であれば200が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-direction-register", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path, {"text":"directon test"})
        self.assertEquals(response.status_code, 200)

    def test_add_favorite_recipe_nologin(self):
        """
        url: recipes-favorite-add
        ログインしていない場合はログインページへリダイレクトされ、302が返される。
        """
        recipe_id = 1
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_add_favorite_recipe_login_another_user(self):
        """
        url:recipes-favorite-add
        ログイン者と対象のレシピの作成者が違う場合、200が返される。
        """
        recipe_id = 1
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 200)

    def test_add_favorite_recipe_nonexistence_recipe(self):
        """
        url:recipes-favorite-add
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)


    def test_add_favorite_recipe_login(self):
        """
        url:recipes-favorite-add
        ログイン済みでレシピの作成者であれば403が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)

    def test_remove_favorite_recipe_nologin(self):
        """
        url: recipes-favorite-remove
        ログインしていない場合はログインページへリダイレクトされ、302が返される。
        """
        recipe_id = 1
        path = reverse("recipes-favorite-remove", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_remove_favorite_recipe_login_another_user(self):
        """
        url:recipes-favorite-remove
        ログイン者と対象のフェイバリットの作成者が違う場合、404が返される。
        """
        recipe_id = 1
        self.client.login(**user2)
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)
        
        path = reverse("recipes-favorite-remove", kwargs={"recipe_id":recipe_id})
        self.client.login(**user3)
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 404)

    def test_remove_favorite_recipe_nonexistence_recipe(self):
        """
        url:recipes-favorite-remove
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-favorite-remove", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)

    def test_remove_favorite_recipe_login(self):
        """
        url:recipes-favorite-remove
        ログイン済みで対象のフェイバリットの作成者であれば200が返される。
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        self.client.login(**user2)
        path = reverse("recipes-favorite-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)
        path = reverse("recipes-favorite-remove", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)

    def test_vote_to_recipe_nologin(self):
        """
        url: recipes-vote
        ログインしていない場合はログインページへリダイレクトされ、302が返される。
        """
        recipe_id = 1
        path = reverse("recipes-vote", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_vote_to_recipe_login_another_user(self):
        """
        url:recipes-vote
        作成者ではない場合、成功。
        """
        recipe_id = 1
        self.client.login(**user2)
        path = reverse("recipes-vote", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        self.assertEquals(response.status_code, 200)
    
    def test_vote_to_recipe_noexistence_recipe(self):
        """
        url:recipes-vote
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-vote", kwargs={"recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)
    
    def test_vote_to_recipe_login(self):
        """
        url:recipes-vote
        レシピ作成者の場合、403が返される。
        """
        recipe_id = 1
        self.client.login(**user1)
        path = reverse("recipes-vote", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEquals(recipe.user.username, user1["username"])
        self.assertEquals(response.status_code, 403)

    def test_comment_to_recipe_nologin(self):
        """
        url: recipes-comment-add
        ログインしていない場合はログインページへリダイレクトされ、302が返される。
        """
        recipe_id = 1
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_comment_to_recipe_login_another_user(self):
        """
        url:recipes-comment-add
        作成者ではない場合、成功。is_moderatedはFalse。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        redirect_url = reverse("recipes-show", kwargs={"recipe_id":recipe.id})
        self.assertRedirects(response, redirect_url, 302, 200)
        comment = Comment.objects.get(text=post_data["text"])
        self.assertFalse(comment.is_moderated)
    
    def test_comment_to_recipe_noexistence_recipe(self):
        """
        url:recipes-comment
        指定されたIDが無い場合、404が返される。
        """
        recipe_id = 10000
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)
    
    def test_comment_to_recipe_login(self):
        """
        url:recipes-comment-add
        作成者の場合、成功。is_moderatedはTrue。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user1)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertNotEquals(recipe.user.username, user2["username"])
        redirect_url = reverse("recipes-show", kwargs={"recipe_id":recipe.id})
        self.assertRedirects(response, redirect_url, 302, 200)
        comment = Comment.objects.get(text=post_data["text"])
        self.assertTrue(comment.is_moderated)

    def test_delete_comment_nologin(self):
        """
        url:recipes-comment-delete
        ログインしていない場合、ログインページにリダイレクトされる。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user1)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-delete", kwargs={"comment_id":comment.id})
        self.client.logout()
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_delete_comment_login_comment_owner(self):
        """
        url:recipes-comment-delete
        コメントを書いたユーザの場合、成功。コメントは削除される。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-delete", kwargs={"comment_id":comment.id})
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)
        try:
            comment = Comment.objects.get(text=post_data["text"])
            self.fail("comment wasn't deleted.")
        except Comment.DoesNotExist:
            pass
    
    def test_delete_comment_login_another_user(self):
        """
        url:recipes-comment-delete
        コメントを書いたユーザでも、レシピ作成者でもない場合、403。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-delete", kwargs={"comment_id":comment.id})
        self.client.login(**user3)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)
        try:
            comment = Comment.objects.get(text=post_data["text"])
        except Comment.DoesNotExist:
            self.fail("comment was deleted.")
    
    def test_delete_comment_noexistence(self):
        """
        url:recipes-comment-delete
        指定されたIDが無い場合、404が返される。
        """
        post_data = {"text":"Test Comment"}
        path = reverse("recipes-comment-add", kwargs={"recipe_id":1})
        self.client.login(**user2)
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-delete", kwargs={"comment_id":10000})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)
        try:
            comment = Comment.objects.get(text=post_data["text"])
        except Comment.DoesNotExist:
            self.fail("comment was deleted.")
    
    def test_delete_comment_login(self):
        """
        url:recipes-comment-delete
        レシピ作成者の場合、成功。コメントは削除される。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-delete", kwargs={"comment_id":comment.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)
        try:
            comment = Comment.objects.get(text=post_data["text"])
            self.fail("comment wasn't deleted.")
        except Comment.DoesNotExist:
            pass
    
    def test_approve_comment_nologin(self):
        """
        url:recipes-comment-approve
        ログインしていない場合、ログインページにリダイレクトされる。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user1)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-approve", kwargs={"comment_id":comment.id})
        self.client.logout()
        response = self.client.post(path)
        login_page_url = reverse("recipes-users-login")+"?next="+path
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_approve_comment_login_another_user(self):
        """
        url:recipes-comment-delete
        レシピ作成者ではない場合、403。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-approve", kwargs={"comment_id":comment.id})
        response = self.client.post(path)
        self.assertEquals(response.status_code, 403)
        comment = Comment.objects.get(text=post_data["text"])
        self.assertFalse(comment.is_moderated)
    
    def test_approve_comment_noexistence(self):
        """
        url:recipes-comment-approve
        指定されたIDが無い場合、404が返される。
        """
        post_data = {"text":"Test Comment"}
        path = reverse("recipes-comment-add", kwargs={"recipe_id":1})
        self.client.login(**user2)
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-approve", kwargs={"comment_id":10000})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 404)
    
    def test_approve_comment_login(self):
        """
        url:recipes-comment-approve
        レシピ作成者の場合、成功。コメントは承認される。
        """
        recipe_id = 1
        post_data = {"text":"Test Comment"}
        self.client.login(**user2)
        path = reverse("recipes-comment-add", kwargs={"recipe_id":recipe_id})
        response = self.client.post(path, post_data)
        comment = Comment.objects.get(text=post_data["text"])
        path = reverse("recipes-comment-approve", kwargs={"comment_id":comment.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEquals(response.status_code, 200)
        comment = Comment.objects.get(text=post_data["text"])
        self.assertTrue(comment.is_moderated)

    def test_search_recipes(self):
        """
        url:recipes-search
        全てのユーザに対して200を返す。
        """
        path = reverse("recipes-search", kwargs={"query":"test"})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)


class ContestsViewsTest(TestCase):
    """
    recipes.views.contests.pyに対する機能テスト。
    """

    fixtures = ["test_recipes.json", "test_auth.json"]

    def test_show_current_contest_list_current(self):
        """
        url: recipes-contests-current
        日付が範囲内のお題は表示される。
        """
        current = Contest.objects.get(pk=1)
        current.published_at = datetime.now() - timedelta(days=1)
        current.closed_at = datetime.now() + timedelta(days=1)
        current.save()
        path = reverse("recipes-contests-current")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, current.name.encode("utf-8"))

    def test_show_current_contest_list_old(self):
        """
        url: recipes-contests-current
        日付が古いお題は表示されない。
        """
        old = Contest.objects.get(pk=1)
        old.published_at = datetime.now() - timedelta(days=2)
        old.closed_at = datetime.now() - timedelta(days=1)
        old.save()
        path = reverse("recipes-contests-current")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, old.name.encode("utf-8"))

    def test_show_current_contest_list_future(self):
        """
        url: recipes-contests-current
        日付が未来のお題は表示されない。
        """
        future = Contest.objects.get(pk=1)
        future.published_at = datetime.now() + timedelta(days=1)
        future.closed_at = datetime.now() + timedelta(days=2)
        future.save(force_update=True)
        path = reverse("recipes-contests-current")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, future.name.encode("utf-8"))

    def test_show_closed_contest_list_current(self):
        """
        url: recipes-contests-closed
        日付が範囲内のお題は表示されない。
        """
        current = Contest.objects.get(pk=1)
        current.published_at = datetime.now() - timedelta(days=1)
        current.closed_at = datetime.now() + timedelta(days=1)
        current.save(force_update=True)
        path = reverse("recipes-contests-closed")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        for contest in response.context[0]["page_obj"].object_list:
            if contest.pk == current.pk:
                self.fail("Future contest shouldn't be displayed.")

    def test_show_closed_contest_list_old(self):
        """
        url: recipes-contests-closed
        日付が古いお題は表示される。
        """
        old = Contest.objects.get(pk=1)
        old.published_at = datetime.now() - timedelta(days=2)
        old.closed_at = datetime.now() - timedelta(days=1)
        old.save(force_update=True)
        path = reverse("recipes-contests-closed")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, old.name.encode("utf-8"))

    def test_show_closed_contest_list_future(self):
        """
        url: recipes-contests-closed
        日付が未来のお題は表示されない。
        """
        future = Contest.objects.get(pk=1)
        future.published_at = datetime.now() + timedelta(days=1)
        future.closed_at = datetime.now() + timedelta(days=2)
        future.save()
        path = reverse("recipes-contests-closed")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, future.name.encode("utf-8"))

    def test_show_contest_current(self):
        """
        url: recipes-contests-show
        日付が範囲内のお題は表示される。
        TODO: ひもづいたドラフトでないレシピが表示される。
        """
        current = Contest.objects.get(pk=1)
        current.published_at = datetime.now() - timedelta(days=1)
        current.closed_at = datetime.now() + timedelta(days=1)
        current.save()
        path = reverse("recipes-contests-show", kwargs={"contest_id":current.pk})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]["contest"].pk, current.pk)

    def test_show_contest_old(self):
        """
        url: recipes-contests-show
        日付が過去のお題は表示される。
        TODO: 優秀レシピが表示される。
        """
        old = Contest.objects.get(pk=1)
        old.published_at = datetime.now() - timedelta(days=2)
        old.closed_at = datetime.now() - timedelta(days=1)
        old.save()
        path = reverse("recipes-contests-show", kwargs={"contest_id":old.pk})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0]["contest"].pk, old.pk)

    def test_show_contest_future(self):
        """
        url: recipes-contests-show
        日付が未来のお題は表示されない。
        """
        future = Contest.objects.get(pk=1)
        future.published_at = datetime.now() + timedelta(days=1)
        future.closed_at = datetime.now() + timedelta(days=2)
        future.save()
        path = reverse("recipes-contests-show", kwargs={"contest_id":future.pk})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_recipes(self):
        """
        url: recipes-contests-recipes
        ドラフトではないお題にひもづいたレシピが表示される。
        """
        contest = Contest.objects.get(pk=1)
        recipe = Recipe.objects.get(pk=1)
        recipe.contest = contest
        recipe.is_draft = False
        recipe.save()
        path = reverse("recipes-contests-recipes", kwargs={"contest_id":contest.pk})
        response = self.client.get(path)
        self.assertContains(response, recipe.name.encode("utf-8"))

    def test_show_recipes_draft(self):
        """
        url: recipes-contests-recipes
        ドラフトであるレシピは表示されない。
        """
        contest = Contest.objects.get(pk=1)
        recipe = Recipe.objects.get(pk=1)
        recipe.contest = contest
        recipe.is_draft = True
        recipe.save()
        path = reverse("recipes-contests-recipes", kwargs={"contest_id":contest.pk})
        response = self.client.get(path)
        self.assertNotContains(response, recipe.name.encode("utf-8"))

    def test_submit_recipe_nologin(self):
        """
        url: recipes-contests-submit-recipe
        ログインしていない場合は302
        """
        contest_id = 1
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = None
        recipe.save()
        path = reverse("recipes-contests-submit-recipe", 
                       kwargs={"contest_id":contest_id,
                               "recipe_id":recipe_id})
        response = self.client.post(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_submit_recipe_login_another_user(self):
        """
        url: recipes-contests-submit-recipe
        レシピ作成者ではない場合は403
        """
        contest_id = 1
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = None
        recipe.save()
        self.assertEqual(recipe.user.username, user1.get("username"))
        path = reverse("recipes-contests-submit-recipe", 
                       kwargs={"contest_id":contest_id,
                               "recipe_id":recipe_id})
        self.client.login(**user2)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 403)

    def test_submit_recipe_login(self):
        """
        url: recipes-contests-submit-recipe
        成功
        """
        contest_id = 1
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = None
        recipe.save()
        self.assertEqual(recipe.user.username, user1.get("username"))
        path = reverse("recipes-contests-submit-recipe", 
                       kwargs={"contest_id":contest_id,
                               "recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEqual(recipe.contest_id, contest_id)

    def test_submit_recipe_login_submitted(self):
        """
        url: recipes-contests-submit-recipe
        既にお題に提出している場合は403
        """
        contest_id = 1
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        contest = Contest.objects.get(pk=contest_id)
        recipe.contest = contest
        recipe.save()
        self.assertEqual(recipe.user.username, user1.get("username"))
        path = reverse("recipes-contests-submit-recipe", 
                       kwargs={"contest_id":contest_id,
                               "recipe_id":recipe_id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 403)

    def test_search_contests(self):
        path = reverse("recipes-contests-search", 
                       kwargs={"query":"test"})
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
    

class UsersViewsTest(TestCase):
    """
    recipes.views.users.pyに対する機能テスト。
    """

    fixtures = ["test_recipes.json", "test_auth.json"]

    def test_new_get(self):
        """
        url: recipes-users-new
        200が返される。
        """
        path = reverse("recipes-users-new")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_new_post(self):
        """
        url: recipes-users-new
        ユーザが作成される。is_active == False
        """
        post_data = {"email":"test4@marici.co.jp",
                     "password1":"password",
                     "password2":"password",
                     "first_name":"test4",
                     "gender":"female",
                     "birth_year":"1970",
                     "prefecture":"tokyo",
                     "agree_tos":"true"}
        path = reverse("recipes-users-new")
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        user = response.context[0]["created_user"]
        self.assertEquals(user.first_name, post_data["first_name"])
    
    def test_validate(self):
        """
        url: recipes-users-validate
        成功した場合。is_active == Trueになる。
        """
        post_data = {"email":"test4@marici.co.jp",
                     "password1":"password",
                     "password2":"password",
                     "first_name":"test4",
                     "gender":"female",
                     "birth_year":"1970",
                     "prefecture":"tokyo",
                     "agree_tos":"true"}
        path = reverse("recipes-users-new")
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        user = response.context[0]["created_user"]
        profile = user.get_profile()
        path = reverse("recipes-users-validate", 
                       kwargs={"key":profile.validation_key})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        user = response.context[0]["created_user"]
        self.assertTrue(user.is_active)
    
    def test_validate_imcomplete(self):
        """
        url: recipes-users-validate
        失敗した場合。is_active == Falseのままである。
        """
        post_data = {"email":"test4@marici.co.jp",
                     "password1":"password",
                     "password2":"password",
                     "first_name":"test4",
                     "gender":"female",
                     "birth_year":"1970",
                     "prefecture":"tokyo",
                     "agree_tos":"true"}
        path = reverse("recipes-users-new")
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        user = response.context[0]["created_user"]
        profile = user.get_profile()
        path = reverse("recipes-users-validate", 
                       kwargs={"key":"invalid_key"})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
        user = User.objects.get(email=post_data["email"])
        self.assertFalse(user.is_active)
    
    def test_inactivate_get_login(self):
        """
        url: recipes-users-inactivate
        ログインしていれば200を返す。
        """
        path = reverse("recipes-users-inactivate")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_inacctivate_post_login(self):
        """
        url: recipes-users-inactivate
        ログインしていれば200を返す。is_active == Falseになる。
        """
        user = User.objects.get(username=user1["username"])
        self.assertTrue(user.is_active)
        path = reverse("recipes-users-inactivate")
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=user1["username"])
        self.assertFalse(user.is_active)
    
    def test_show(self):
        """
        url: recipes-users-show
        200を返す。
        """
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-show", 
                       kwargs={"user_id":user.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_show_awarded(self):
        """
        結果が発表されている場合、受賞レシピにマークを表示
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now()
        contest.finished_at = datetime.now()
        contest.is_finished = True
        contest.save()
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-show", 
                       kwargs={"user_id":recipe.user.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon_awardedstatus.jpg")
        
    def test_show_awarded_unfinished(self):
        """
        結果が発表されていない場合、受賞レシピにマークを表示しない
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now() + timedelta(days=1)
        contest.finished_at = datetime.now() + timedelta(days=1)
        contest.is_finished = True
        contest.save()
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-show", 
                       kwargs={"user_id":recipe.user.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "icon_awardedstatus.jpg")
        
    def test_show_noexistence(self):
        """
        url: recipes-users-show
        ユーザが存在しない場合。404を返す。
        """
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-show", 
                       kwargs={"user_id":10000})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)
    
    def test_show_home(self):
        """
        url: recipes-users-home
        ログインしていれば200を返す。
        """
        path = reverse("recipes-users-home")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u"ホーム".encode("utf-8"))
    
    def test_show_home_nologin(self):
        """
        url: recipes-users-home
        ログインしていなければログインページにリダイレクトされる。
        """
        path = reverse("recipes-users-home")
        response = self.client.get(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_show_home_awarded(self):
        """
        結果が発表されている場合、受賞レシピにマークを表示
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now()
        contest.finished_at = datetime.now()
        contest.is_finished = True
        contest.save()
        self.assertEquals(user1["username"], recipe.user.username)
        path = reverse("recipes-users-home")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon_awardedstatus.jpg")
        
    def test_show_home_awarded_unfinished(self):
        """
        結果が発表されていない場合、受賞レシピにマークを表示しない
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now() + timedelta(days=1)
        contest.finished_at = datetime.now() + timedelta(days=1)
        contest.is_finished = True
        contest.save()
        self.assertEquals(user1["username"], recipe.user.username)
        path = reverse("recipes-users-home")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "icon_itemstatus03.jpg")
        
    def test_show_recipe_list_login(self):
        """
        url: recipes-users-recipes
        自分のレシピの場合。下書きも表示される。
        """
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-recipes", 
                       kwargs={"user_id":user.id})
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_show_recipe_list_login_another_user(self):
        """
        url: recipes-users-recipes
        他のユーザの場合。下書きは表示されない。
        """
        user = User.objects.get(username=user1["username"])
        path = reverse("recipes-users-recipes", 
                       kwargs={"user_id":user.id})
        self.client.login(**user2)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_show_recipe_list_awarded(self):
        """
        結果が発表されている場合、受賞レシピにマークを表示
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now()
        contest.finished_at = datetime.now()
        contest.is_finished = True
        contest.save()
        path = reverse("recipes-users-recipes", 
                       kwargs={"user_id":recipe.user.id})
        self.client.login(**user2)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "icon_awardedstatus.jpg")
        
    def test_show_recipe_list_awarded_unfinished(self):
        """
        結果が発表されていない場合、受賞レシピにマークを表示しない
        """
        recipe_id = 1
        recipe = Recipe.objects.get(pk=recipe_id)
        recipe.contest = contest = Contest.objects.get(pk=1)
        recipe.is_awarded = True
        recipe.save()
        contest.closed_at = datetime.now() + timedelta(days=1)
        contest.finished_at = datetime.now() + timedelta(days=1)
        contest.is_finished = True
        contest.save()
        path = reverse("recipes-users-recipes", 
                       kwargs={"user_id":recipe.user.id})
        self.client.login(**user2)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "icon_awardedstatus.jpg")
        
    def test_edit_profile_get_nologin(self):
        """
        url: recipes-users-edit-profile
        ログインしていなければログインページにリダイレクトされる。
        """
        path = reverse("recipes-users-edit-profile")
        response = self.client.get(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_edit_profile_get_login(self):
        """
        url: recipes-users-edit-profile
        フォームが表示される。
        """
        path = reverse("recipes-users-edit-profile")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
    
    def test_edit_profile_post_nologin(self):
        """
        url: recipes-users-edit-profile
        ログインしていなければログインページにリダイレクトされる。
        """
        post_data = {"prefecture":"tokyo"}
        path = reverse("recipes-users-edit-profile")
        response = self.client.post(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_edit_profile_post_login(self):
        """
        url: recipes-users-edit-profile
        データが更新される。
        """
        post_data = {"nickname":"test", "prefecture":"hokkaido"}
        path = reverse("recipes-users-edit-profile")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        self.assertRedirects(response, path, 302, 200)
        user = User.objects.get(username=user1.get("username"))
        profile = UserProfile.objects.get(user=user)
        self.assertEquals(profile.prefecture, post_data.get("prefecture"))
    
    def test_add_favorite_user_nologin(self):
        """
        url: recipes-users-favorite-add
        ログインしていなければログインページにリダイレクトされる。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        path = reverse("recipes-users-favorite-add", kwargs={"user_id":u2.id})
        response = self.client.post(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)
        
    def test_add_favorite_user_login_another_user(self):
        """
        url: recipes-users-favorite-add
        他のユーザの場合、FavoriteUserに保存される。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        path = reverse("recipes-users-favorite-add", kwargs={"user_id":u2.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        fav = FavoriteUser.objects.get(user=u1, target=u2)
    
    def test_add_favorite_user_login_nonexistence(self):
        """
        url: recipes-users-favorite-add
        ターゲットが存在しない場合、保存されず404が返される。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        u2.is_active = False
        u2.save()
        path = reverse("recipes-users-favorite-add", kwargs={"user_id":u2.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 404)
    
    def test_add_favorite_user_login(self):
        """
        url: recipes-users-favorite-add
        自分自身をフェイバリットに追加しようとすると403
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        path = reverse("recipes-users-favorite-add", kwargs={"user_id":u1.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 403)
        try:
            fav = FavoriteUser.objects.get(user=u1, target=u2)
        except FavoriteUser.DoesNotExist, e:
            pass
        else:
            self.fail("FavoriteUser should not be added.")
    
    def test_remove_favorite_user_nologin(self):
        """
        url: recipes-users-favorite-remove
        ログインしていなければログインページにリダイレクトされる。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        path = reverse("recipes-users-favorite-remove", kwargs={"user_id":u2.id})
        response = self.client.post(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)
            
    def test_remove_favorite_user_login_another_user(self):
        """
        url: recipes-users-favorite-remove
        他のユーザの場合、削除されず404が返る。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        path = reverse("recipes-users-favorite-remove", kwargs={"user_id":u2.id})
        self.client.login(**user3)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 404)
        try:
            fav = FavoriteUser.objects.get(user=u1, target=u2)
        except FavoriteUser.DoesNotExist, e:
            self.fail("FavoriteUser should not be removed.")
    
    def test_remove_favorite_user_login_nonexistence(self):
        """
        url: recipes-users-favorite-remove
        対象がアクティブでなくても削除は可能。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        u2.is_active = False
        u2.save()
        path = reverse("recipes-users-favorite-remove", kwargs={"user_id":u2.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        try:
            fav = FavoriteUser.objects.get(user=u1, target=u2)
        except FavoriteUser.DoesNotExist, e:
            pass
        else:
            self.fail("FavoriteUser should be removed.")
    
    def test_remove_favorite_user_login(self):
        """
        url: recipes-users-favorite-remove
        成功。削除され200が返る。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        path = reverse("recipes-users-favorite-remove", kwargs={"user_id":u2.id})
        self.client.login(**user1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)
        try:
            fav = FavoriteUser.objects.get(user=u1, target=u2)
        except FavoriteUser.DoesNotExist, e:
            pass
        else:
            self.fail("FavoriteUser should be removed.")
    
    def test_show_favorite_recipes_nonexistence(self):
        """
        url: recipes-users-favorite-recipes-show
        ユーザがアクティブでない場合、404が返る。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u1.is_active = False
        u1.save()
        path = reverse("recipes-users-favorite-recipes-show", kwargs={"user_id":u1.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_favorite_users(self):
        """
        url: recipes-users-favorite-recipes-show
        200が返る。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        self.assertTrue(u1.is_active)
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        path = reverse("recipes-users-favorite-users-show", kwargs={"user_id":u1.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, u2.first_name.encode("utf-8"))

    def test_show_favorite_users_nonexistence(self):
        """
        url: recipes-users-favorite-recipes-show
        ユーザがアクティブでない場合、404が返る。
        """
        u1 = User.objects.get(username=user1.get("username"))
        u2 = User.objects.get(username=user2.get("username"))
        fav = FavoriteUser.objects.create(user=u1, target=u2)
        u1.is_active = False
        u1.save()
        path = reverse("recipes-users-favorite-users-show", kwargs={"user_id":u1.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def test_show_owner_comments_nologin(self):
        """
        url: recipes-users-home-comments
        ログインしていなければログインページにリダイレクトされる。
        """
        u2 = User.objects.get(username=user2.get("username"))
        recipe = Recipe.objects.get(pk=1)
        Comment.objects.create(user=u2, recipe=recipe, text=u"Test Comment 1")
        path = reverse("recipes-users-home-comments")
        response = self.client.get(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)
    
    def test_show_owner_comments_login_another_user(self):
        """
        url: recipes-users-home-comments
        オーナー本人しかコメントを参照できない。
        """
        u2 = User.objects.get(username=user2.get("username"))
        recipe = Recipe.objects.get(pk=1)
        Comment.objects.create(owner=recipe.user, user=u2, recipe=recipe, 
            text="Test Comment 1")
        path = reverse("recipes-users-home-comments")
        self.client.login(**user3)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Test Comment 1")
    
    def test_show_owner_comments_login(self):
        """
        url: recipes-users-recipes
        コメントをつけられた本人は参照することができる。
        """
        u2 = User.objects.get(username=user2.get("username"))
        recipe = Recipe.objects.get(pk=1)
        self.assertEquals(recipe.user.username, user1.get("username"))
        Comment.objects.create(owner=recipe.user, user=u2, recipe=recipe, 
            text="Test Comment 1")
        path = reverse("recipes-users-home-comments")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Comment 1")
    
    def test_change_email_get_nologin(self):
        """
        url: recipes-users-email-change
        ログインしていなければログインページにリダイレクトされる。
        """
        path = reverse("recipes-users-email-change")
        response = self.client.get(path)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_change_email_get(self):
        """
        url: recipes-users-email-change
        フォームが表示される。
        """
        path = reverse("recipes-users-email-change")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_change_email_post_nologin(self):
        """
        url: recipes-users-email-change
        ログインしていなければログインページにリダイレクトされる。
        """
        post_data = {"email":"testuser1-change@marici.co.jp"}
        path = reverse("recipes-users-email-change")
        response = self.client.post(path, post_data)
        login_page_url = "%s?next=%s" % (reverse("recipes-users-login"), path)
        self.assertRedirects(response, login_page_url, 302, 200)

    def test_change_email_post(self):
        """
        url: recipes-users-email-change
        成功。
        """
        post_data = {"email":"testuser1-change@marici.co.jp"}
        path = reverse("recipes-users-email-change")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        u1 = User.objects.get(username=user1.get("username"))
        profile = u1.get_profile()
        self.assertEquals(profile.pending_email, post_data.get("email"))

    def test_validate_change_email_another_key(self):
        """
        url: recipes-users-validate-email
        間違ったURLではメールアドレスは変更されない。
        """
        post_data = {"email":"testuser1-change@marici.co.jp"}
        path = reverse("recipes-users-email-change")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        u1 = User.objects.get(username=user1.get("username"))
        path = reverse("recipes-users-validate-email", kwargs={"user_id":u1.pk, "key":"invalid_key"})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 403)
        u1 = User.objects.get(pk=u1.pk)
        self.assertNotEquals(u1.email, post_data.get("email"))

    def test_validate_change_email(self):
        """
        url: recipes-users-validate-email
        正しくバリデーションURLにアクセスすると、メールアドレスが変更される。
        """
        post_data = {"email":"testuser1-change@marici.co.jp"}
        path = reverse("recipes-users-email-change")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        self.assertEqual(response.status_code, 200)
        u1 = User.objects.get(username=user1.get("username"))
        profile = u1.get_profile()
        path = reverse("recipes-users-validate-email", 
            kwargs={"user_id":u1.pk, "key":profile.validation_key})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        u1 = User.objects.get(pk=u1.pk)
        self.assertEquals(u1.email, post_data.get("email"))
        self.assertEquals(u1.username, forms.email_to_username(post_data.get("email")))

    def test_login_get_nologin(self):
        """
        url: recipes-users-login
        ログインフォームが表示される。
        """
        path = reverse("recipes-users-login")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_login_get(self):
        """
        url: recipes-users-login
        ログインフォームが表示される。
        """
        path = reverse("recipes-users-login")
        self.client.login(**user1)
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)

    def test_login_post_nologin(self):
        """
        url: recipes-users-login
        ログインさせる。
        """
        post_data = {"email":"testuser1@marici.co.jp", "password":"password"}
        path = reverse("recipes-users-login")
        response = self.client.post(path, post_data)
        home_url = reverse("recipes-users-home")
        self.assertRedirects(response, home_url, 302, 200)

    def test_login_post(self):
        """
        url: recipes-users-login
        ログインさせる。
        """
        post_data = {"email":"testuser1@marici.co.jp", "password":"password"}
        path = reverse("recipes-users-login")
        self.client.login(**user1)
        response = self.client.post(path, post_data)
        home_url = reverse("recipes-users-home")
        self.assertRedirects(response, home_url, 302, 200)

    def test_show_active_users(self):
        """
        url: active-users
        200を返す。
        """
        path = reverse("active-users")
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)


