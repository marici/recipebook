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
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from maricilib.search.solrsearch import SolrConnection
import models

class BaseModelSearcher(object):
    pass


class SQLModelSearcher(BaseModelSearcher):

    def search(self, model_manager, queries, fields=None, page=1, per_page=10):
        start = per_page * (page-1)
        if getattr(settings, "SEARCH_USE_SQL_FULLTEXT", False):
            entities = models.Entity.objects.search(model_manager.model, queries)
        else:
            entities = models.Entity.objects.contains(model_manager.model, queries)
        ids = [ e.object_id for e in entities[start:start+per_page] ]
        instances = ids and model_manager.filter(id__in=ids) or []
        return {"hits":entities.count(), "object_list":instances}


class SolrModelSearcher(BaseModelSearcher):

    def __init__(self, url):
        self.url = url

    @classmethod
    def instance_pk(cls, doc_id):
        return str(doc_id).split(".")[1]
        
    def search(self, model_manager, queries, fields=None, page=1, per_page=10):
        fq = "+type:%s" % model_manager.model.__name__
        start = per_page * (page-1)
        results = SolrConnection.search(self.url, queries, fields, fq=fq,
                                        start=start, rows=per_page)
        ids = [ self.instance_pk(r["id"]) for r in results ]
        instances = ids and model_manager.filter(id__in=ids) or []
        return {"hits":results.hits, "object_list":instances}


class BaseModelIndexer(object):
    
    @classmethod
    def doc_id(cls, instance):
        return "%s.%s" % (instance.__class__.__name__, instance.pk)
    
    def add(self, instance):
        if hasattr(instance, "__need_add_index__") and \
                instance.__need_add_index__():
            d = getattr(instance, "__indexdoc__", None)
            if d is None: return
            self.add_doc(instance, d())
        elif hasattr(instance, "__need_delete_index__") and \
                instance.__need_delete_index__():
            self.delete(instance)

    def add_doc(self, instance, data):
        raise NotImplementedError

    def delete(self, instance):
        raise NotImplementedError


class SQLModelIndexer(BaseModelIndexer):

    def add_doc(self, instance, data):
        entity = models.Entity.objects.get_entity(instance)
        if entity is None:
            entity = models.Entity.objects.create_entity(instance)
        else:
            entity.set_doc(data)
            entity.save()

    def delete(self, instance):
        entity = models.Entity.objects.get_entity(instance)
        if entity is not None:
            entity.delete()


class SolrModelIndexer(BaseModelIndexer):
       
    def add_doc(self, instance, data):
        doc = dict(data)
        doc["type"] = instance.__class__.__name__
        doc["id"] = self.doc_id(instance)
        SolrConnection.add(self.url, [doc])
            
    def delete(self, instance):
        doc_id = self.doc_id(instance)
        SolrConnection.delete(self.url, doc_id)


if getattr(settings, "SEARCH_USE_SOLR", False):
    indexer = hasattr(settings, "SEARCH_INDEXER_URL") \
        and SolrModelIndexer(settings.SEARCH_INDEXER_URL) or None
else:
    indexer = SQLModelIndexer()
    
if getattr(settings, "SEARCH_USE_SOLR", False):
    searcher = hasattr(settings, "SEARCH_SEARCHER_URL") \
        and SolrModelIndexer(settings.SEARCH_SEARCHER_URL) or None
else:
    searcher = SQLModelSearcher()

# シグナルレシーバ
def add_document(sender, **kwargs):
    instance = kwargs.get("instance")
    if indexer: indexer.add(instance)

def delete_document(sender, **kwargs):
    instance = kwargs.get("instance")
    if indexer: indexer.delete(instance)

def register_index(model):
    post_save.connect(add_document, sender=model)
    post_delete.connect(delete_document, sender=model)
