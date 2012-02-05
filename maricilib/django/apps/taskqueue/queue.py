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
from recipebook.maricilib.taskqueue import TaskQueue, default_queue

taskqueue = None

def get_taskqueue():
    global taskqueue
    if taskqueue is None:
        kwargs = {}
        def _setting(key, setting_name):
            if hasattr(settings, setting_name):
                kwargs[key] = getattr(settings, setting_name)
        _setting("backend", "QUEUE_BACKEND")
        _setting("user", "QUEUE_USER")
        _setting("password", "QUEUE_PASSWORD")
        _setting("host", "QUEUE_HOST")
        _setting("port", "QUEUE_PORT")
        _setting("timeout", "QUEUE_TIMEOUT")
        taskqueue = TaskQueue(**kwargs)
    return taskqueue

def set_taskqueue(tq):
    global taskqueue
    taskqueue = tq
