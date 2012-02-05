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

class DoTaskLog(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"タスク実行ログ"
        
    start = models.DateTimeField(u"処理開始日時")
    end = models.DateTimeField(u"処理終了日時")
    task_name = models.CharField(u"タスククラス名", max_length=30)
    module_name = models.CharField(u"モジュール名", max_length=200)
    success_count = models.IntegerField(u"成功件数")
    error_count = models.IntegerField(u"エラー件数")
    total_count = models.IntegerField(u"トータル件数")
    
    def __unicode__(self):
        return "%s.%s" % (self.module_name, self.task_name)
    
class ErrorLog(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = u"タスクエラーログ"
        
    task_name = models.CharField(u"タスククラス名", max_length=30)
    module_name = models.CharField(u"モジュール名", max_length=200)
    args = models.TextField(u"タスク引数")
    text = models.TextField(u"エラー内容")
    reported_at = models.DateTimeField(u"報告日時")

    def __unicode__(self):
        return "%s.%s" % (self.module_name, self.task_name)
    
    def abbr(self):
        return self.text[:50]
    
