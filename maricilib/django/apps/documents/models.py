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
from django.contrib.markup.templatetags.markup import textile, markdown, restructuredtext
import managers

class Image(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"画像"
        
    name = models.CharField(u"名前", max_length=50)
    file = models.ImageField(u"画像ファイル", upload_to="documents")
    
    def URL(self):
        return self.file.url
    
    
class MarkupSyntax(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"マークアップ文法"
        
    name = models.CharField(u"名前", max_length=20)
    
    def __unicode__(self):
        return self.name

class Document(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"ドキュメント"
    
    objects = managers.DocumentManager()
    
    title = models.CharField(u"見出し", max_length=50)
    label = models.SlugField(u"ラベル", db_index=True,
         help_text=u"""
         URLの一部になります。英数字とアンダーバーのみ使うことができます。
         他のドキュメントと重複してはいけません。
         """)
    body = models.TextField(u"本文", blank=True, null=True)
    image = models.ImageField(u"画像", upload_to="documents", 
                              blank=True, null=True)
    image_description = models.TextField(u"画像の説明", blank=True, null=True)
    number = models.IntegerField(u"整列順", default=1)
    syntax = models.ForeignKey(MarkupSyntax, verbose_name=u"マークアップ文法", 
                               blank=True, null=True,
                               help_text=u"本文のマークアップ文法を指定できます。")
    parent = models.ForeignKey("self", verbose_name=u"親文書", 
                               blank=True, null=True)
    created_at = models.DateTimeField(u"作成日時", auto_now_add=True)
    updated_at = models.DateTimeField(u"最終更新日時", editable=False)
    creator = models.ForeignKey(User, editable=False, verbose_name=u"作成者",
                                related_name="create_document_set")
    updater = models.ForeignKey(User, editable=False, verbose_name=u"更新者",
                                related_name="update_document_set")

    def __unicode__(self):
        return self.title
    
    def get_markuped_body(self):
        if not self.syntax:
            return self.body
        syntax_name = self.syntax.name
        if syntax_name == "textile":
            return textile(self.body)
        elif syntax_name == "markdown":
            return markdown(self.body)
        elif syntax_name == "restructuredtext":
            return restructuredtext(self.body)
        else:
            return self.body
    markuped_body = property(get_markuped_body)
    
    def get_children(self):
        return self.__class__.objects.get_children(self)
    children = property(get_children)
    
