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
from django.http import HttpResponseNotAllowed
from maricilib.multimethod import multifunc, ByContentMultiMethod

class ByDjangoHTTP(ByContentMultiMethod):
    POST = "POST"
    GET = "GET"
    
    def get_key(self, request, *args, **kwargs):
        return (request.method.upper(),)
    
    def notfound(self):
        return lambda *args, **kwargs: HttpResponseNotAllowed([]) # TODO: 正しいメソッド名のリストを返す
    
    def __getattribute__(self, name):
        if name == "__name__":
            func = self.keymap.values()[0]
            return func.__name__
        elif name == "__module__":
            func = self.keymap.values()[0]
            return func.__module__
        else:
            return ByContentMultiMethod.__getattribute__(self, name)


def postmethod(func):
    return multifunc(ByDjangoHTTP, ByDjangoHTTP.POST)(func)

def getmethod(func):
    return multifunc(ByDjangoHTTP, ByDjangoHTTP.GET)(func)
