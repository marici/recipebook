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
from django.contrib import admin
import models

class FeedBackCategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.FeedBackCategory, FeedBackCategoryAdmin)


class FeedBackAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "path", "text", "created_at", "checked", 
                    "checked_at", "owner")
    list_filter = ("checked", )
    date_hierarchy = "created_at"
    
    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        obj.checked_at = datetime.now()
        obj.save()

admin.site.register(models.FeedBack, FeedBackAdmin)
