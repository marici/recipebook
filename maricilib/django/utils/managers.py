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
from recipebook.maricilib.warnings import module_deprecated
module_deprecated(__name__, "recipebook.maricilib.django.db.models.managers")

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.db import models

class DailyScoreManager(models.Manager):
    """
    DailyScoreクラス継承テーブルに対する操作の実装クラス。
    """
    qlimit_min = 100
    
    def get_score_object(self, object, score):
        try:
            score_obj = self.get(object=object, scored_at=date.today())
        except self.model.DoesNotExist, e:
            score_obj = None
        return score_obj
    
    def add(self, object, score):
        score_obj = self.get_score_object(object, score)
        if not score_obj:
            score_obj = self.create(object=object, scored_at=now, score=score)
        return score_obj
        
    def update_add(self, object, score):
        score_obj = self.get_score_object(object, score)
        if score_obj:
            score_obj.score += score
            score_obj.save()
        else:
            score_obj = self.create(object=object, score=score)
        return score_obj
        
    def get_ranked_query_set(self, start, end=None, limit=None):
        end = end or date.today()
        limit = limit or self.qlimit_min
        qs = self.filter(scored_at__lt=end)
        qs = qs.filter(scored_at__gte=start)
        qs = qs.order_by("-score")
        return qs[:limit]
    
    def get_ranked_objects(self, start, end=None, limit=5, queryset=None):
        if isinstance(start, datetime):
            start = start.date()
        if not queryset:
            end = end or date.today()
            qlimit = max(self.qlimit_min, ((end - start).days+1) * limit)
            queryset = self.get_ranked_query_set(start, end, qlimit)
        score_dict = {}
        score_obj_dict = {}
        for score_obj in queryset:
            obj_id = getattr(score_obj, "object_id")
            score = score_dict.get(obj_id, 0)
            score_dict[obj_id] = score + score_obj.score
            score_obj_dict[obj_id] = score_obj
        ranked_list = sorted(score_dict.iteritems(), 
                             lambda x, y: cmp(y[1], x[1]))
        return [ score_obj_dict.get(obj_id).object 
                for obj_id, score in ranked_list[:limit] ]
        
