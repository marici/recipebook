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
import copy, logging
from django.db import models
import fields
try:
    from maricilib.django.core.files.storage import S3Storage
    s3_storage = S3Storage()
except Exception, e:
    logging.warn("S3Storage is not available. %s" % e)
    s3_storage = None

class S3SyncModelBase(models.base.ModelBase):
    """
    Djangoモデルクラスの定義に含まれるファイルフィールドインスタンスを複製し、
    Amazon S3格納用のフィールドを追加定義するメタクラス。
    複製の対象となるのは、maricilib.django.db.fields.S3Sync*Fieldのインスタンスである。
    モデルクラスには以下のフィールドが追加される。

     * [fieldname]_s3 - ストレージをS3としたファイルおよび画像フィールド
     * [fieldname]_s3_sync - S3への格納フラグのためのBooleanField

    [fieldname]_s3の定義はオリジナルのフィールドをコピーするが、以下の点が異なる。

     * storage: maricilib.django.core.files.storage.S3Storageインスタンス
     * blank: True
     * null: True
     * editable: False
     * db_column: [origfieldのdb_column]_s3 (db_columnが設定されている場合)

    さらに、モデルクラスにsync_[fieldname]プロパティを追加する。このプロパティは、
    [fieldname]_s3_syncフィールドの値がTrueの場合は[fieldname]_s3フィールドの値を、
    Falseの場合は[fieldname]フィールドの値を返す。
    """

    def __new__(cls, name, bases, dict):
        for key, value in dict.items():
            if isinstance(value, fields.S3SyncField):
                s3_name, s3_flag_name, prop_name = cls.get_names(key)
                dict[s3_name] = cls.create_s3_field(value)
                dict[s3_flag_name] = models.BooleanField(editable=False)
                dict[prop_name] = cls.create_property(key)
        return super(S3SyncModelBase, cls).__new__(cls, name, bases, dict)

    @classmethod
    def get_names(cls, field_name):
        s3_field_name = "%s_s3" % field_name
        s3_flag_name = "%s_sync" % s3_field_name
        sync_prop_name = "sync_%s" % field_name
        return s3_field_name, s3_flag_name, sync_prop_name

    @classmethod
    def create_s3_field(cls, field):
        s3_field = copy.deepcopy(field)
        if s3_storage:
            s3_field.storage = s3_storage
        s3_field.blank = True
        s3_field.null = True
        s3_field.editable = False
        if field.db_column:
            s3_field.db_column = "%s_s3" % field.db_column
        return s3_field

    @classmethod
    def create_property(cls, key):
        s3_name, s3_flag_name, prop_name = cls.get_names(key)
        def get_sync_value(self):
            if getattr(self, s3_flag_name):
                return getattr(self, s3_name)
            else:
                return getattr(self, key)
        return property(get_sync_value)
    
