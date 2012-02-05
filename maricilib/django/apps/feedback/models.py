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
from django.db import models
from django.contrib.auth.models import User

class FeedBackCategory(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"カテゴリ"
    name = models.CharField(u"カテゴリ名", max_length=50)
    
    def __unicode__(self):
        return self.name

class FeedBack(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"フィードバック"
    user = models.ForeignKey(User, verbose_name=u"ユーザ", null=True, editable=False)
    path = models.CharField(u"該当箇所", max_length=100, null=True, blank=True)
    category = models.ForeignKey(FeedBackCategory, verbose_name=u"ご意見の種類", 
                                 null=True, blank=True)
    text = models.TextField(u"お気づきの内容")
    created_at = models.DateTimeField(u"投稿日時", auto_now_add=True, editable=False,
                                      db_index=True)
    owner = models.ForeignKey(User, verbose_name=u"確認者", null=True, editable=False,
                             related_name="own_feedback_set")
    checked = models.BooleanField(u"確認済み", db_index=True)
    checked_at = models.DateTimeField(u"確認日時", null=True, editable=False)
    
    def __unicode__(self):
        username = self.user.username if self.user else u"ゲスト"
        return u"%s のフィードバック" % self.user.username
