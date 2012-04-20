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
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template import loader, Context
from django.utils import simplejson
from maricilib.django.apps.feedback import forms

def submit(request, send_mail_func=send_mail):
    """
    フィードバックを受け付けます。
    FEEDBACK_SENDMAILがTrueの場合、管理者向けメールを送信します。
    send_mail_funcでメールの送信関数を渡すことができます。
    送信関数の定義はdjango.core.mail.send_mailに準じます。
    """
    form = forms.FeedBackForm(request.POST, prefix="feedback")
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.user = request.user
        feedback.path = request.POST.get("path")
        feedback.save()
        if getattr(settings, "FEEDBACK_SENDMAIL", False):
            c = Context({"feedback":feedback})
            t = loader.get_template("feedback/email/notification.txt")
            subject = u"フィードバックが追加されました"
            body = t.render(c)
            send_mail_func(subject, body, 
                           getattr(settings, "FEEDBACK_SENDMAIL_FROM", None), 
                           getattr(settings, "FEEDBACK_SENDMAIL_TO", None),
                           fail_silently=True)
        d = {"status":"success", "message":u"ご意見をお預かりしました。ありがとうございました。"}
    else:
        d = {"status":"error", "message":u"内容に不足があります。本文が必須です。"}
    json = simplejson.dumps(d)
    return HttpResponse(json, mimetype="application/json")

