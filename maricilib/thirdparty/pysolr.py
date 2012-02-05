# -*- coding: utf-8 -*-
"""
All we need to create a Solr connection is a url.

>>> #conn = Solr('http://127.0.0.1:8983/solr/')
>>> conn = Solr('http://127.0.0.1:8080/solr/default/')

First, completely clear the index.

>>> conn.delete(q='*:*')

For now, we can only index python dictionaries. Each key in the dictionary
will correspond to a field in Solr.

>>> docs = [
...     {'id': 'testdoc.1', 'order_i': 1, 'name': 'document 1', 'text': u'Paul Verlaine'},
...     {'id': 'testdoc.2', 'order_i': 2, 'name': 'document 2', 'text': u'Владимир Маякoвский'},
...     {'id': 'testdoc.3', 'order_i': 3, 'name': 'document 3', 'text': u'test'},
...     {'id': 'testdoc.4', 'order_i': 4, 'name': 'document 4', 'text': u'test'}
... ]


We can add documents to the index by passing a list of docs to the connection's
add method.

>>> conn.add(docs)

>>> results = conn.search('Verlaine')
>>> len(results)
1

>>> results = conn.search(u'Владимир')
>>> len(results)
1


Simple tests for searching. We can optionally sort the results using Solr's
sort syntax, that is, the field name and either asc or desc.

>>> results = conn.search('test', sort='order_i asc')
>>> for result in results:
...     print result['name']
document 3
document 4

>>> results = conn.search('test', sort='order_i desc')
>>> for result in results:
...     print result['name']
document 4
document 3


To update documents, we just use the add method.

>>> docs = [
...     {'id': 'testdoc.4', 'order_i': 4, 'name': 'document 4', 'text': u'blah'}
... ]
>>> conn.add(docs)

>>> len(conn.search('blah'))
1
>>> len(conn.search('test'))
1


We can delete documents from the index by id, or by supplying a query.

>>> conn.delete(id='testdoc.1')
>>> conn.delete(q='name:"document 2"')

>>> results = conn.search('Verlaine')
>>> len(results)
0


Docs can also have multiple values for any particular key. This lets us use
Solr's multiValue fields.

>>> docs = [
...     {'id': 'testdoc.5', 'cat': ['poetry', 'science'], 'name': 'document 5', 'text': u''},
...     {'id': 'testdoc.6', 'cat': ['science-fiction',], 'name': 'document 6', 'text': u''},
... ]

>>> conn.add(docs)
>>> results = conn.search('cat:"poetry"')
>>> for result in results:
...     print result['name']
document 5

>>> results = conn.search('cat:"science-fiction"')
>>> for result in results:
...     print result['name']
document 6

>>> results = conn.search('cat:"science"')
>>> for result in results:
...     print result['name']
document 5

"""

# TODO: unicode support is pretty sloppy. define it better.

from httplib import HTTPConnection
from urllib import urlencode
from urlparse import urlsplit
from datetime import datetime, date
from time import strptime
try:
    # for python 2.5
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        # use etree from lxml if it is installed
        from lxml import etree as ET
    except ImportError:
        try:
            # use cElementTree if available
            import cElementTree as ET
        except ImportError:
            try:
                from elementtree import ElementTree as ET
            except ImportError:
                raise ImportError("No suitable ElementTree implementation was found.")

__all__ = ['Solr']

class SolrError(Exception):
    pass

class Results(object):
    def __init__(self, docs, hits):
        self.docs = docs
        self.hits = hits

    def __len__(self):
        return len(self.docs)

    def __iter__(self):
        return iter(self.docs)

class Solr(object):
    def __init__(self, url):
        self.url = url
        scheme, netloc, path, query, fragment = urlsplit(url)
        netloc = netloc.split(':')
        self.host = netloc[0]
        if len(netloc) == 1:
            self.host, self.port = netloc[0], None
        else:
            self.host, self.port = netloc
        self.path = path.rstrip('/')

    def _select(self, params):
        # encode the query as utf-8 so urlencode can handle it
        params['q'] = params['q'].encode('utf-8')
        path = '%s/select/?%s' % (self.path, urlencode(params))
        conn = HTTPConnection(self.host, self.port)
        conn.request('GET', path)
        return conn.getresponse()

    def _update(self, message):
        """
        Posts the given xml message to http://<host>:<port>/solr/update and
        returns the result.
        """
        path = '%s/update/' % self.path
        conn = HTTPConnection(self.host, self.port)
        conn.request('POST', path, message, {'Content-type': 'text/xml'})
        return conn.getresponse()

    def _extract_error(self, response):
        """
        Extract the actual error message from a solr response. Unfortunately,
        this means scraping the html.
        """
        et = ET.parse(response)
        return et.findtext('body/pre')

    # Converters #############################################################

    def _from_python(self, value):
        """
        Converts python values to a form suitable for insertion into the xml
        we send to solr.
        """
        if isinstance(value, datetime):
            value = value.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        elif isinstance(value, date):
            value = value.strftime('%Y-%m-%dT00:00:00.000Z')
        elif isinstance(value, bool):
            if value:
                value = 'true'
            else:
                value = 'false'
        else:
            value = unicode(value)
        return value

    def bool_to_python(self, value):
        """
        Convert a 'bool' field from solr's xml format to python and return it.
        """
        if value == 'true':
            return True
        elif value == 'false':
            return False

    def str_to_python(self, value):
        """
        Convert an 'str' field from solr's xml format to python and return it.
        """
        return unicode(value)

    def int_to_python(self, value):
        """
        Convert an 'int' field from solr's xml format to python and return it.
        """
        return int(value)

    def date_to_python(self, value):
        """
        Convert a 'date' field from solr's xml format to python and return it.
        """
        # this throws away fractions of a second
        return datetime(*strptime(value[:-5], "%Y-%m-%dT%H:%M:%S")[0:6])

    def float_to_python(self, value):
        """
        Convert a 'float' field from solr's xml format to python and return it.
        """
        return float(value)

    def double_to_python(self, value):
        """
        Convert a 'double' field from solr's xml format to python and return
        it. Since Python does not have separate type for double, this is the
        same as float.
        """
        return self.float_to_python(value)

    # API Methods ############################################################

    def search(self, q, fq=None, sort=None, start=None, rows=None, **kwargs):
        """Performs a search and returns the results."""
        params = {'q': q}
        params.update(kwargs)
        if fq:
            params['fq'] = fq
        if start:
            params['start'] = start
        if rows:
            params['rows'] = rows
        if sort:
            params['sort'] = sort
        response = self._select(params)
        if response.status != 200:
            raise SolrError(self._extract_error(response))

        # TODO: make result retrieval lazy and allow custom result objects
        # also, this has become rather ugly and definitely needs some cleanup.
        et = ET.parse(response)
        result = et.find('result')
        hits = int(result.get('numFound'))
        docs = result.findall('doc')
        results = []
        for doc in docs:
            result = {}
            for element in doc.getchildren():
                try:
                    if element.tag == 'arr':
                        result_val = []
                        for array_element in element.getchildren():
                            converter_name = '%s_to_python' % array_element.tag
                            converter = getattr(self, converter_name)
                            result_val.append(converter(array_element.text))
                    else:
                        converter_name = '%s_to_python' % element.tag
                        converter = getattr(self, converter_name)
                        result_val = converter(element.text)
                    result[element.get('name')] = result_val
                except:
                    pass
            results.append(result)
        return Results(results, hits)

    def add(self, docs, commit=True):
        """Adds or updates documents. For now, docs is a list of dictionaies
        where each key is the field name and each value is the value to index.
        """
        message = ET.Element('add')
        for doc in docs:
            d = ET.Element('doc')
            for key, value in doc.items():
                # handle lists, tuples, and other iterabes
                if hasattr(value, '__iter__'):
                    for v in value:
                        f = ET.Element('field', name=key)
                        f.text = self._from_python(v)
                        d.append(f)
                # handle strings and unicode
                else:
                    f = ET.Element('field', name=key)
                    f.text = self._from_python(value)
                    d.append(f)
            message.append(d)
        m = ET.tostring(message)
        response = self._update(m)
        if response.status != 200:
            raise SolrError(self._extract_error(response))
        # TODO: Supposedly, we can put a <commit /> element in the same post body
        # as the add element. That isn't working for some reason, and it would save us
        # an extra trip to the server. This works for now.
        if commit:
            self.commit()

    def delete(self, id=None, q=None, commit=True, fromPending=True, fromCommitted=True):
        """Deletes documents."""
        if id is None and q is None:
            raise ValueError('You must specify "id" or "q".')
        elif id is not None and q is not None:
            raise ValueError('You many only specify "id" OR "q", not both.')
        elif id is not None:
            m = '<delete><id>%s</id></delete>' % id
        elif q is not None:
            m = '<delete><query>%s</query></delete>' % q
        response = self._update(m)
        if response.status != 200:
            raise SolrError(self._extract_error(response))
        # TODO: Supposedly, we can put a <commit /> element in the same post body
        # as the delete element. That isn't working for some reason, and it would save us
        # an extra trip to the server. This works for now.
        if commit:
            self.commit()

    def commit(self):
        response = self._update('<commit />')
        if response.status != 200:
            raise SolrError(self._extract_error(response))

    def optimize(self):
        response = self._update('<optimize />')
        if response.status != 200:
            raise SolrError(self._extract_error(response))

if __name__ == "__main__":
    import doctest
    doctest.testmod()
