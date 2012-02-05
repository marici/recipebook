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

try:
    from mysql_replicated.decorators import _use_state
except:
    def _use_state(state):
        return _fake_use_state(state)

def _fake_use_state(state):
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        wrapper.__module__ = func.__module__
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

def use_state(state):
    if settings.DATABASE_ENGINE == "mysql_replicated":
        return _use_state(state)
    else:
        return _fake_use_state(state)
        
use_master = use_state("master")
use_slave = use_state("slave")
