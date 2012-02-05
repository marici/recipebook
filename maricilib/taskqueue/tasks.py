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

class InvalidTaskArgs(Exception):
    pass


class Task(object):

    def __init__(self, kwargs):
        """
        渡された引数の検証を行い、self.[attribute]に展開します。
        """
        self.kwargs = self.validate_kwargs(kwargs)
        self.__dict__.update(self.kwargs)

    def get_task_info(self):
        return (self.__class__.__name__,
            self.__class__.__module__,
            self.kwargs)

    def validate_kwargs(self, kwargs):
        """
        インスタンス生成時にパラメータを検証するメソッドです。
        サブクラスではkwargsをチェックし、問題があればInvalidTaskArgsをraiseします。
        戻り値は検証後のkwargsです。
        """
        return kwargs

    def do(self):
        """
        実際の処理を行うメソッドです。
        サブクラスではself.[attribute]を使って処理を行います。
        """
        raise NotImplementedError()

    @classmethod
    def from_model(cls, instance):
        raise NotImplementedError()
    
    def validate_has_all_key(self, keys, kwargs):
        for key in keys:
            if not kwargs.has_key(key):
                raise InvalidTaskArgs("kwargs must have %s" % ",".join(keys))
        return kwargs
    
    def validate_has_any_key(self, keys, kwargs):
        for key in keys:
            if kwargs.has_key(key):
                return kwargs
        raise InvalidTaskArgs("kwargs must have any in %s" % ",".join(keys))


class SendEmailTask(Task):
    def do(self):
        pass


class DummyTask(Task):
    def do(self): pass
    

class ErrorTask(Task):
    def do(self): raise Exception("error")
    
