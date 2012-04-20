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
from django.core.mail import send_mail
from django.conf import settings
from maricilib import load_class
from maricilib.taskqueue.tasks import Task
from maricilib.django.db.models.base import S3SyncModelBase
from maricilib.django.db.models.fields import S3SyncField

class SendEmailTask(Task):
    """
    Djangoのメール送信APIを利用したメール送信タスクです。
    
    @param subject: メールサブジェクト
    @param body: メール本文
    @param from_address: 送信元アドレス
    @param to_list: 送信先アドレスのリスト
    """
    def validate_kwargs(self, kwargs):
        return self.validate_has_all_key(("subject", "body", "from_address", 
                                          "to_list"), kwargs)
    
    def do(self):
        send_mail(self.subject, self.body, self.from_address, self.to_list)
    
    
class SyncS3Task(Task):
    """
    S3SyncModelBaseのフィールド拡張仕様にもとづきAmazon S3にファイルをコピーするタスクです。
    
    @param classname: モデルクラス名
    @param module: モデルクラスの属するモジュール
    @param pk: インスタンスのプライマリキー値
    """
    def validate_kwargs(self, kwargs):
        return self.validate_has_all_key(("classname", "module", "pk"), 
                                         kwargs)

    def do(self):
        if not settings.USE_AWS: return
        cls = load_class(self.classname, self.module)
        try:
            inst = cls.objects.get(pk=self.pk)
        except:
            return
        for key, value in inst.__dict__.items():
            attribute = getattr(inst, key)
            field = getattr(attribute, "field", None)
            if isinstance(field, S3SyncField):
                s3_name, s3_flag_name, prop_name = \
                    S3SyncModelBase.get_names(key)
                if not hasattr(inst, s3_name): continue
                S3SyncField.send_to_s3(inst, key, s3_name, s3_flag_name)

    @classmethod
    def from_model(cls, instance):
        """
        モデルインスタンスからタスクを生成します。
        """
        return cls({"classname":instance.__class__.__name__,
                    "module":instance.__class__.__module__,
                    "pk":instance.pk})
    
class DeleteS3Task(Task):
    """
    Amazon S3からファイルを削除するタスクです。
    
    @param name: ファイルパス
    """
    def validate_kwargs(self, kwargs):
        return self.validate_has_all_key(("name", ), kwargs)

    def do(self):
        if not settings.USE_AWS: return
        from recipebook.maricilib.django.core.files.storage import S3Storage
        s3_storage = S3Storage()
        s3_storage.delete(self.name)
