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
from django.contrib.contenttypes.models import ContentType

class EntityManager(models.Manager):

    def contains(self, model, queries):
        """
        指定されたモデルに対するEntityをLIKE検索します。
        """
        content_type = ContentType.objects.get_for_model(model)
        qs = self.filter(content_type=content_type)
        for query in queries:
            qs.filter(text__icontains=query)
        return qs

    def search(self, model, queries):
        """
        指定されたモデルに対するEntityを全文検索します。
        """
        content_type = ContentType.objects.get_for_model(model)
        query = " ".join([ u"+%s" % q for q in queries ])
        return self.filter(content_type=content_type, text__search=query)

    def get_entity(self, content_object):
        """
        指定されたcontent_objectに対するEntityインスタンスを返します。
        なければNoneを返します。
        """
        try:
            content_type = ContentType.objects.get_for_model(content_object.__class__)
            entity = self.get(content_type=content_type,
                              object_id=content_object.pk)
        except self.model.DoesNotExist, e:
            entity = None
        return entity

    def create_entity(self, content_object):
        """
        指定されたcontent_objectに対するEntityインスタンスを作成します。
        """
        entity = self.model(content_object=content_object, text='')
        doc = content_object.__indexdoc__()
        entity.set_doc(doc)
        entity.save()
        return entity

