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
from django.core.paginator import Paginator as BasePaginator
from django.core.paginator import Page as BasePage
from django.http import Http404

class Paginator(BasePaginator):
    """
    django.core.paginator.Paginatorクラスの拡張。
    このクラスのインスタンスがpageメソッドで返すPageインスタンスは、
    around_page_rangeプロパティを持つ。
    """
    def page(self, number):
        try:
            page = super(Paginator, self).page(number)
        except:
            raise Http404
        page.__class__ = Page
        return page


class Page(BasePage):
    """
    django.core.paginator.Pageクラスの拡張。
    around_page_rangeプロパティは、省略されたページ番号のタプルを返す。
    """
    around_num = 10
    
    def _get_around_page_range(self):
        num_pages = self.paginator.num_pages
        start = 1
        end = num_pages + 1
        if self.around_num < num_pages:
            start = max(start, self.number - self.around_num / 2)
            end = min(end, start + self.around_num)
        return range(start, end)
    around_page_range = property(_get_around_page_range)

    
if __name__ == "__main__":
    def test(objects, per_page, page_num, start_number):
        paginator = Paginator(objects, per_page)
        page = paginator.page(page_num)
        page_range = page.around_page_range
        print page_range
        assert page_range[0] == start_number
        assert page_range[-1] <= paginator.num_pages
        
    objects = range(500)
    test(objects, 5, 10, 5)
    test(objects, 10, 1, 1)
    test(objects, 10, 2, 1)
    test(objects, 10, 10, 5)
    test(objects, 10, 49, 44)
    test(objects, 10, 50, 45)
    try:
        test(objects, 10, 51, 46)
        assert False
    except:
        assert True
