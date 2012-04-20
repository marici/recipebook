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
from django.core.management.base import BaseCommand
from maricilib.django.apps.taskqueue.queue import get_taskqueue, default_queue
from maricilib.django.apps.taskqueue.models import DoTaskLog, ErrorLog

from datetime import datetime

class Command(BaseCommand):

    def handle(self, *args, **opts):
        start_time = datetime.now()

        taskqueue = get_taskqueue()
        queue_name = default_queue
        if 0 < len(args):
            queue_name = args[0]

        tasklogs = {}
        for task in taskqueue.receive_tasks(queue_name):
            name, module, kwargs = task.get_task_info()
            if not tasklogs.has_key(name):
                log = DoTaskLog()
                log.start = start_time
                log.task_name = name
                log.module_name = module
                log.success_count = 0
                log.error_count = 0
                tasklogs.update({name:log})
            try:
                task.do()
            except Exception, e:
                # エラー件数をタスク別にカウント
                # エラーログを保存
                log.error_count+=1
                elog = ErrorLog()
                elog.task_name = name
                elog.module_name = module
                elog.args = str(task.kwargs)
                elog.text = str(e)
                elog.reported_at = datetime.now()
                elog.save()
            else:
                # 成功件数をタスク別にカウント
                log.success_count+=1
        end_time = datetime.now()
        # タスク別に成功/失敗件数
        for task_name in tasklogs:
            log = tasklogs[task_name]
            log.end = end_time
            log.total_count = log.success_count+log.error_count
            log.save()
        # エラー通知メールを送信？
