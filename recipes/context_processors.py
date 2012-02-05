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
from datetime import datetime, timedelta
from django.core.cache import cache
from recipebook.recipes.models import Contest, UserProfile, Recipe
from recipebook.recipes.views import users as users_view

def side1(request):
    active_beginners = cache.get("views_top_active_beginners")
    if active_beginners is None:
        three_days_ago = datetime.now() - timedelta(days=3)
        active_beginners = UserProfile.objects.active_beginners(three_days_ago)
        cache.set("views_top_active_beginners", active_beginners)
    current_contests = Contest.objects.get_current_contests()
    u_and_p = users_view.get_active_users_and_profiles()
    return {"active_beginners":active_beginners,
            "current_contests":current_contests,
            "users_and_profiles":u_and_p[:5]}
