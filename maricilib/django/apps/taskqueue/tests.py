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
from django.test import TestCase
from maricilib.taskqueue import TaskQueue, tasks
from maricilib.taskqueue.backends import dummy
from maricilib.django.apps.taskqueue import queue
from maricilib.django.apps.taskqueue.models import DoTaskLog, ErrorLog
from maricilib.django.apps.taskqueue.management.commands import dotask

class CommandTest(TestCase):
    """
    コマンドのテストです。
    """
    def test_do_task_command(self):
        taskqueue = TaskQueue(operation_cls=dummy.QueueOperation)
        
        def send_tasks(task_cls, queue_name, number):
            for x in xrange(number):
                taskqueue.send_task(task_cls({}), queue_name)
                
        send_tasks(tasks.DummyTask, "queue1", 100)
        send_tasks(tasks.ErrorTask, "queue1", 10)
        send_tasks(tasks.DummyTask, "queue2", 50)
        send_tasks(tasks.ErrorTask, "queue2", 30)
        
        queue.set_taskqueue(taskqueue)
        dotask.Command().handle("queue1")
        dotask.Command().handle("queue2")
        
        log_qs = DoTaskLog.objects.all()
        self.assertEqual(log_qs.count(), 4)
        self.assertEqual(log_qs.filter(task_name=tasks.DummyTask.__name__).count(), 2)
        self.assertEqual(log_qs.filter(task_name=tasks.ErrorTask.__name__).count(), 2)
        
        error_log_qs = ErrorLog.objects.all()
        self.assertEqual(error_log_qs.count(), 40)
        self.assertEqual(error_log_qs.filter(task_name=tasks.ErrorTask.__name__).count(), 40)
