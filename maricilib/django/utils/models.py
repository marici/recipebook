# coding: utf-8
from recipebook.maricilib.warnings import module_deprecated
module_deprecated(__name__, "recipebook.maricilib.django.db.models")

from django.db import models
from recipebook.maricilib.django.db.models import managers

class DailyScore(models.Model):
    """
    ランキングに必要な日毎のスコア。
    継承クラスはobjectクラス属性にForeignKeyインスタンスをセットしなければならない。
    """
    class Meta:
        abstract = True
        
    objects = managers.DailyScoreManager()
    
    object = None
    score = models.IntegerField(u"スコア")
    scored_at = models.DateField(u"スコア加算日", auto_now_add=True)
    
    def __unicode__(self):
        return self.object.__unicode__()
