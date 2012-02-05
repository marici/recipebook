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
from __future__ import with_statement
import unicodedata
from recipebook.maricilib.thirdparty.pysolr import *

class SolrConnection(object):
    
    def __init__(self, url, commit=False, optimize=False):
        self.url = url
        self.commit = commit
        self.optimize = optimize
        self._solr = Solr(self.url)
        
    def __enter__(self):
        return self._solr
    
    def __exit__(self, _type, _value, _tb):
        if self.commit:
            self._solr.commit()
        if self.optimize:
            self._solr.optimize()

    @classmethod
    def search(cls, url, queries, fields=None, fq=None, sort=None, start=None, 
               rows=None, normalize=False):
        if normalize:
            query = cls.normalize(query)
        if fields:
            query = " ".join(["%s:%s" % (f, q) for f, q in zip(fields, queries)])
        else:
            query = " ".join(queries)
        with cls(url) as _solr:
            results = _solr.search(query, fq, sort, start, rows)
        return results
    
    @classmethod
    def add(cls, url, docs):
        with cls(url, commit=True) as _solr:
            _solr.add(docs)

    @classmethod
    def delete(cls, url, id=None, q=None):
        with cls(url, commit=True) as _solr:
            _solr.delete(id, q)
    
    @classmethod
    def normalize(cls, text):
        return unicodedata.normalize("NFKC", text)
