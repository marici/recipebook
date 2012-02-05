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
from recipebook.maricilib import load_class
from recipebook.maricilib.taskqueue import backends
from recipebook.maricilib.taskqueue.backends import base as backbase
from tasks import Task

default_queue = "default"

class BackendNotFound(Exception):
    pass

class TaskQueue(object):

    def __init__(self, *args, **kwargs):
        operation_cls = kwargs.pop("operation_cls", None)
        if operation_cls is None:
            backend = kwargs.pop("backend", None)
            if backend:
                module = getattr(backends, backend, None)
                if module:
                    operation_cls = module.QueueOperation
                else:
                    raise BackendNotFound("backend module '%s' was not found." % backend)
        if operation_cls and issubclass(operation_cls, backbase.BaseQueueOperation):
            self.operation = operation_cls(*args, **kwargs)
        else:
            self.operation = backends.dummy.QueueOperation(*args, **kwargs)

    def send_task(self, task, queue_name=default_queue):
        if not isinstance(task, Task):
            raise TypeError("arg 1 must be a 'Task' instance")
        self.operation.send_task(task, queue_name)

    def receive_tasks(self, queue_name=default_queue):
        for task_info in self.operation.receive_tasks(queue_name):
            class_name, module_name, kwargs = task_info
            cls = load_class(class_name, module_name)
            task = cls(kwargs)
            yield task
