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

class SiteNews(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"サイトのニュース"
        
    title = models.CharField(u"見出し", max_length=50)
    url = models.URLField(u"URL", null=True, blank=True)
    text = models.TextField(u"本文", null=True, blank=True)
    image = models.ImageField(u"写真・画像",
                              upload_to=u"images/sitenews", 
                              null=True, blank=True)
    is_open = models.BooleanField(u"公開", default=False)
    published_at = models.DateTimeField(u"公開日時", db_index=True)
    created_at = models.DateTimeField(u"作成日時",
                                      auto_now_add=True,
                                      editable=False)
    updated_at = models.DateTimeField(u"最終変更日時",
                                      editable=False)
    user = models.ForeignKey(User, verbose_name=u"作成者", editable=False)
    
    def has_detail(self):
        return self.text
    
    def __unicode__(self):
        return self.title
