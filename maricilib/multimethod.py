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

class MultiMethod(object):

    def __init__(self, name):
        self.name = name
        self.keymap = {}
        self.orig_self = None

    def __call__(self, *args, **kwargs):
        if self.orig_self:
            return self.find(*args, **kwargs)(self.orig_self, *args, **kwargs)
        else:
            return self.find(*args, **kwargs)(*args, **kwargs)

    def find(self, *args, **kwargs):
        raise NotImplemented()

    def register(self, function, *keys):
        if keys in self.keymap:
            raise TypeError("duplicate registration")
        self.keymap[keys] = function

    def notfound(self):
        raise TypeError("no match")


class ByArgTypeMultiMethod(MultiMethod):

    def find(self, *args, **kwargs):
        types = tuple(arg.__class__ for arg in args)
        function = self.keymap.get(types)
        if function is None:
            return self.notfound()
        return function


class ByContentMultiMethod(MultiMethod):

    def get_key(self, *args, **kwargs):
        raise NotImplemented()

    def find(self, *args, **kwargs):
        key = self.get_key(*args, **kwargs)
        function = self.keymap.get(key)
        if function is None:
            return self.notfound()
        return function


_registry = {}

def _multimethod(bound, mmcls, *keys):
    def register(function):
        function = getattr(function, "__lastreg__", function)
        name = (function.__module__, function.__name__)
        mm = _registry.get(name)
        if mm is None:
            mm = _registry[name] = mmcls(name)
        mm.register(function, *keys)
        mm.__lastreg__ = function
        if bound:
            mm.orig_self = self
        return mm
    return register

def multimethod(mmcls, *keys):
    return _multimethod(True, mmcls, *keys)

def multifunc(mmcls, *keys):
    return _multimethod(False, mmcls, *keys)
 
