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
from recipebook.maricilib.stomp import Stomper
from recipebook.maricilib.taskqueue.backends.base import BaseQueueOperation

class QueueOperation(BaseQueueOperation):

    def __init__(self, host="127.0.0.1", port=61613, user="", password="",
                 timeout=10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.timeout = timeout

    def send_task(self, task, queue_name):
        s = Stomper()
        s.connect(host=self.host, port=self.port, user=self.user, 
                  password=self.password, timeout=self.timeout)
        s.send_as_json("/queue/%s" % queue_name, task.get_task_info(), True)
        s.disconnect()

    def receive_tasks(self, queue_name):
        s = Stomper()
        s.connect(host=self.host, port=self.port, user=self.user, 
                  password=self.password, timeout=self.timeout)
        s.subscribe("/queue/%s" % queue_name)
        while True:
            f, json_obj = s.receive_as_json()
            if not f:
                break
            yield json_obj
        s.disconnect()
