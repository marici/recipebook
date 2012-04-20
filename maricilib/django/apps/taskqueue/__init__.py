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
from django.db.models import signals
from django.conf import settings
from maricilib.django.apps.taskqueue.queue import get_taskqueue

# シグナルレシーバ
def send_post_save_task(sender, **kwargs):
    if kwargs.get("created"):
        send_task("__post_save_task__", sender, **kwargs)

def send_post_delete_task(sender, **kwargs):
    send_task("__post_delete_task__", sender, **kwargs)

def send_task(method_name, sender, **kwargs):
    instance = kwargs.get("instance")
    taskmaker = getattr(instance, method_name, None)
    if taskmaker is not None:
        task = taskmaker()
        if type(task) in (list, tuple):
            queue_name = task[1]
            task = task[0]
        else:
            queue_name = sender.__module__
        if task: get_taskqueue().send_task(task, queue_name)

def register_task(model):
    if getattr(settings, "TASKQUEUE_USE_SIGNAL", True):
        signals.post_save.connect(send_post_save_task, model)
        signals.post_delete.connect(send_post_delete_task, model)
