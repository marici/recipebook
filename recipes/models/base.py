# -*- coding: utf-8 -*-
'''
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
'''
import os
import uuid
import itertools
from datetime import datetime, date, timedelta
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
from maricilib.django.shortcuts import get_object
from maricilib.django.db.models.base import S3SyncModelBase
from maricilib.django.db.models import fields
from maricilib.django.apps.taskqueue import register_task
from maricilib.django.apps.taskqueue.tasks import SyncS3Task, DeleteS3Task
from maricilib.django.apps.taskqueue.queue import get_taskqueue
from maricilib.django.apps.search import register_index
from maricilib.django.apps.daily.models import DailyAction, DailyScore
from recipes import managers, scores


class Karma(object):
    '''
    ユーザの操作とそれによるポイント定義
    '''
    act_login = 'act_login'
    act_favorite = 'act_favorite'
    act_vote = 'act_vote'
    act_comment = 'act_comment'
    act_create_recipe = 'act_recipe'
    actions = {act_login: 1, act_favorite: 1, act_vote: 2,
               act_comment: 2, act_create_recipe: 3}

    @classmethod
    def add_karma(cls, user, action, profile=None, save=True):
        if profile is None:
            profile = user.get_profile()
        profile.add_karma(action=Karma.act_favorite)
        if save:
            profile.save()
