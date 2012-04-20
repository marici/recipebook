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
from datetime import datetime
from django import template
from maricilib.django.apps.sitenews.models import SiteNews

register = template.Library()

@register.tag
def get_sitenews_list(parser, token):
    """
    ニュースのリストを取得し、コンテキスト内の変数に格納します。
    パラメータ名・値の組み合わせを指定することができます。
    直接の出力は行いません。
    
    パラメータ名 - 値の説明 (デフォルト値)
    order_by - ソートのキー。 (published_at)
    order - ソート順。昇順なら"asc"。 (desc)
    reverse - リストの格納順。逆にするなら"True"。 (False)
    allow_future - 未来の日付のニュースを表示する場合"True"。 (False)
    limit - 取得する数。 (5)
    as - 代入する変数名。 (sitenews_list)
    
    例:
    {% get_sitenews_list %}
    {% get_sitenews_list limit 10 %}
    {% get_sitenews_list limit 10 order asc as news_list %}
    """
    kwargs = {}
    tokens = token.split_contents()
    if len(tokens) > 1:
        tokens = tokens[1:]
        for start in xrange(0, 7, 2):
            if len(tokens) < start + 1: break
            name, value = tokens[start:start+2]
            if name == "limit":
                value = int(value)
            elif name == "allow_future" or name == "reverse":
                if value.lower() == "true":
                    value = True
                else:
                    value = False
            elif name == "as":
                name = "as_varname"
            kwargs[str(name)] = value
    return SiteNewsListNode(**kwargs)


class SiteNewsListNode(template.Node):
    
    def __init__(self, order_by="published_at", order="desc", limit=5, 
                 allow_future=False, as_varname="sitenews_list",
                 reverse=False):
        self.order_by = order_by
        self.order = order
        self.limit = limit
        self.allow_future = allow_future
        self.as_varname = as_varname
        self.reverse = reverse
    
    def render(self, context):
        qs = self.get_query_set()
        context[self.as_varname] = self.get_context_value_from_query_set(context, qs)
        return ""
    
    def get_query_set(self):
        qs = SiteNews.objects.filter(is_open=True)
        if not self.allow_future:
            now = datetime.now()
            qs = qs.filter(published_at__lt=now)
        order_by = self.order_by
        if self.order != "asc":
            order_by = "-" + order_by
        qs = qs.order_by(order_by)
        return qs[:self.limit]
    
    def get_context_value_from_query_set(self, context, qs):
        value = list(qs)
        if self.reverse:
            value.reverse()
        return value
