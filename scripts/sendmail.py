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
import smtplib
from email.MIMEText import MIMEText

class MailSender(object):

    def __init__(self, smtp_server, smtp_port, smtp_username=None, 
            smtp_pw=None, use_tls=False):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_pw = smtp_pw
        self.use_tls = use_tls

    def send_email(self, to_addr, from_addr, subject, body, encoding="ISO-2022-JP"):
        msg = MIMEText(body.encode(encoding), 'plain', encoding)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addr
    
        smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
        if self.use_tls:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
        if self.smtp_username:
            smtp.login(self.smtp_username, self.smtp_pw)
        smtp.sendmail(from_addr, to_addr, msg.as_string())
        smtp.quit()
