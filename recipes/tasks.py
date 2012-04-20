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
import os
from maricilib.taskqueue.tasks import Task
from django.utils import simplejson
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.sites.models import Site


def send_email(template_path, cdata, subject, to_list):
    '''
    メールを作成し、タスクに登録します。
    '''
    from django.conf import settings
    from django.template import loader, Context
    from maricilib.django.apps.taskqueue.queue import get_taskqueue
    from maricilib.django.apps.taskqueue.tasks import SendEmailTask

    t = loader.get_template(template_path)
    body = t.render(Context(cdata))
    task = SendEmailTask(dict(subject=subject, body=body,
                              from_address=settings.EMAIL_FROM,
                              to_list=to_list))
    get_taskqueue().send_task(task, queue_name=settings.QUEUENAME_EMAIL)


class SubmitRecipeTask(Task):

    def do(self):
        from django.conf import settings
        from django.contrib.auth.models import User
        from recipes.models import Contest, Direction
        from recipes.forms import BackendRecipeForm

        site = Site.objects.get_current()
        user = User.objects.get(pk=self.user_id)
        if self.contest_id:
            contest = Contest.objects.get(pk=self.contest_id)
            if contest.is_closed():
                contest = None
        else:
            contest = None

        profile = user.get_profile()
        if (profile.has_available_token() and
                profile.recipe_token != self.token):
            send_email('recipes/email/submiterror.txt',
                   {'error': (u'管理データが古いか壊れています。'
                       u'もう一度フォーム取得からやり直してください。')},
                   u'[%s] メール投稿のエラー' % site.domain, [self.from_address])

        ing_data = simplejson.dumps(self.ingredients, ensure_ascii=False)
        if hasattr(self, 'photo_path'):
            image_file = open(os.path.join(settings.MEDIA_ROOT,
                self.photo_path))
            file_dict = {'photo': InMemoryUploadedFile(
                image_file, 'photo', self.photo_path,
                    None, os.stat(self.photo_path).st_size,
                    None)}
        else:
            file_dict = {}

        form = BackendRecipeForm(dict(name=self.name,
            introduction=self.introduction,
            tips=self.tips, num_people=self.num_people), file_dict)

        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.user = user
            recipe.contest = contest
            recipe.ingredients = ing_data
            if not self.is_draft:
                recipe.toggle_open_state()
            recipe.save()

            for i, dir in enumerate(self.directions):
                direction = Direction(recipe=recipe, text=dir, number=i + 1)
                direction.save()

            send_email('recipes/email/submitsuccess.txt',
                       {'recipe': recipe},
                       u'[%s] メール投稿の完了' % site.domain, [self.from_address])
        else:
            send_email('recipes/email/submiterror.txt',
                       {'error': u'内容に誤りがあります。\n%s' % u'\n'.join(form.errors)},
                       u'[%s] メール投稿のエラー' % site.domain, [self.from_address])
            raise Exception(form.errors)
