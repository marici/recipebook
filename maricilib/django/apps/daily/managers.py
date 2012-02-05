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
from datetime import date, datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType

class DailyScoreManager(models.Manager):
    
    qlimit_min = 100
    
    def get_score(self, content_object):
        """
        指定されたcontent_objectに対する当日のDailyScoreインスタンスを返します。
        なければNoneを返します。
        """
        try:
            content_type = ContentType.objects.get_for_model(content_object.__class__)
            score_obj = self.get(content_type=content_type,
                                 object_id=content_object.pk, 
                                 scored_at=date.today())
        except self.model.DoesNotExist, e:
            score_obj = None
        return score_obj
    
    def add(self, content_object, score, update=True):
        """
        指定されたcontent_objectに対する当日のDailyScoreインスタンスを返します。
        updateがFalseの場合、なければ作成します。あれば何もせずインスタンスを返します。
        updateがTrueの場合、なければ作成します。あればスコアを加算してインスタンスを返します。
        """
        score_obj = self.get_score(content_object)
        if score_obj and update:
            score_obj.score += score
            score_obj.save()
        elif score_obj is None:
            score_obj = self.create(content_object=content_object, 
                                    score=score)
        return score_obj
        
    def ranked_scores(self, model, start_date, end_date=None, 
                      limit=None):
        content_type = ContentType.objects.get_for_model(model)
        end_date = end_date or date.today()
        limit = limit or self.qlimit_min
        qs = self.filter(content_type=content_type) \
                 .filter(scored_at__lte=end_date) \
                 .filter(scored_at__gte=start_date) \
                 .order_by("-score")
        return qs[:limit]
    
    def get_ranked_objects(self, model, start_date, end_date=None, 
                           limit=10):
        """
        指定されたモデルへのスコアを集計し、降順にソートして、元のインスタンスの
        リストを返します。
        """
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        end_date = end_date or date.today()
        qlimit = max(self.qlimit_min, 
                     ((end_date - start_date).days+1) * limit)
        queryset = self.ranked_scores(model, start_date, 
                                      end_date, qlimit)
        score_dict = {}
        score_obj_dict = {}
        for score_obj in list(queryset):
            obj_id = score_obj.object_id
            score = score_dict.get(obj_id, 0)
            score_dict[obj_id] = score + score_obj.score
            score_obj_dict[obj_id] = score_obj
        ranked_list = sorted(score_dict.iteritems(), 
                             lambda x, y: cmp(y[1], x[1]))
        return [ score_obj_dict.get(obj_id).content_object 
                for obj_id, score in ranked_list[:limit] ]


class DailyActionManager(models.Manager):
    
    def get_action(self, user, content_object, action):
        """
        指定された条件に対する当日のDailyActionインスタンスを返します。
        なければNoneを返します。
        """
        try:
            content_type = ContentType.objects.get_for_model(content_object.__class__)
            action_obj = self.get(user=user,
                                  content_type=content_type,
                                  object_id=content_object.pk, 
                                  done_at=date.today(),
                                  action=action)
        except self.model.DoesNotExist, e:
            action_obj = None
        return action_obj
    
    def is_done(self, user, content_object, action, time=0, update=True):
        """
        指定された条件に対する当日のDailyActionインスタンスを探します。
        インスタンスがない場合、updateがTrueなら作成しFalseを返します。
        updateがFalseなら何もせずFalseを返します。
        インスタンスが存在する場合、加算前の回数がtimeより大きければTrueを返します。
        同時に、updateがTrueなら回数を加算します。updateがFalseなら何もしません。
        """
        action_obj = self.get_action(user, content_object, action)
        if action_obj:
            ret = (time < action_obj.num_times)
            if update:
                action_obj.num_times += 1
                action_obj.save()
            return ret
        else:
            if update:
                action_obj = self.create(user=user,
                                         content_object=content_object, 
                                         action=action)
            return False
        
