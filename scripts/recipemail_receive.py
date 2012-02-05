#!/usr/bin/env python
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
import sys, os, re, unicodedata
from collections import defaultdict
from email.parser import Parser
from recipebook.maricilib.taskqueue import TaskQueue
from recipebook import mailsettings as settings
from recipebook.recipes.tasks import SubmitRecipeTask
from sendmail import MailSender

BR = re.compile(u'[\r\n]+')
QUOTE = re.compile(r'^[>\s]+')
IMAGE_BASEDIR = os.path.join(settings.MEDIA_ROOT, 'users', 'temp')
SEP_LINE = u'----- '

class SubmitError(Exception):
    pass

def get_taskqueue():
    kwargs = {}
    def _setting(key, setting_name):
        if hasattr(settings, setting_name):
            kwargs[key] = getattr(settings, setting_name)
    _setting("backend", "QUEUE_BACKEND")
    _setting("user", "QUEUE_USER")
    _setting("password", "QUEUE_PASSWORD")
    _setting("host", "QUEUE_HOST")
    _setting("port", "QUEUE_PORT")
    _setting("timeout", "QUEUE_TIMEOUT")
    return TaskQueue(**kwargs)

def parse_recipe_body(text):
    user_id = token = contest_id = None
    in_recipe = None
    recipe_body_lines = []
    for line in BR.split(text):
        line = QUOTE.sub('', line)
        line = unicodedata.normalize('NFKC', line) 
        if in_recipe is None and line.startswith(SEP_LINE):
            in_recipe = True
            continue
        elif in_recipe and line.startswith(SEP_LINE):
            in_recipe = False
            continue
        
        if in_recipe:
            recipe_body_lines.append(line)
            
        if line.startswith('*user:'):
            user_id_str = line.split(':')[1].strip()
            if user_id_str.isdigit():
                user_id = int(user_id_str)
        elif line.startswith('*token:'):
            token = line.split(':')[1].strip()
        elif line.startswith('*contest:'):
            contest_id_str = line.split(':')[1].strip()
            if contest_id_str.isdigit():
                contest_id = int(contest_id_str)
        
    name = None
    recipe_dict = defaultdict(list)
    recipe_dict['is_draft'] = True
    for line in recipe_body_lines:
        line = line.strip()
        if line == '': continue
        if line.startswith('*'):
            name = line[1:]
        elif name is not None:
            if name == u'下書きにする/しない' and line == u'しない':
                recipe_dict['is_draft'] = False
            else:
                recipe_dict[name].append(line)
            
    if not (user_id and token):
        raise SubmitError(u'データが壊れています。もう一度フォーム取得からやり直してください。')
    
    if not (recipe_dict.get(u'タイトル') and recipe_dict.get(u'作り方') and 
            recipe_dict.get(u'素材-分量') and recipe_dict.get(u'紹介文')):
        raise SubmitError(u'入力項目に不足があります。タイトル、作り方、素材-分量、紹介文は必須です。') 
    
    d = {'user_id':user_id, 'token':token, 'contest_id':contest_id,
         'is_draft':recipe_dict.get('is_draft', True),
         'name':''.join(recipe_dict.get(u'タイトル')), 
         'directions':recipe_dict.get(u'作り方'),
         'introduction':'\n'.join(recipe_dict.get(u'紹介文')),
         'ingredients':[ i.split(u'-') if u'-' in i else [i, u''] for i in recipe_dict.get(u'素材-分量')],
         'tips':'\n'.join(recipe_dict.get(u'作り方のヒント、コツ')),
         'num_people':recipe_dict.get(u'分量の人数')[0][0]}
    return d

def save_image_file(image_part, user_id):
    filename = image_part.get_filename()
    if not filename:
        ext = mimetypes.guess_extension(image_part.get_type())
        filename = 'part%s' % ext
    image_dir = os.path.join(IMAGE_BASEDIR, str(user_id))
    if not os.path.exists(image_dir):
        os.makedirs(image_dir, 0755)
    image_path = os.path.join(image_dir, filename)
    fp = open(image_path, 'wb')
    fp.write(image_part.get_payload(decode=True))
    fp.close()
    return image_path.replace(settings.MEDIA_ROOT, "")

smtp_server = 'localhost'
smtp_port = 25
def send_error_mail(to_addr, errmsg):
    sender = MailSender(smtp_server, smtp_port)
    sender.send_email(to_addr, 'noreply@recipebook.jp', 
                      u'レシピ投稿のエラー', errmsg)

def main():
    parser = Parser()
    message = parser.parse(sys.stdin)
    from_address = message['From']
    
    taskargs = {'from_address':from_address}
    errors = []
    image_part = None
    
    for part in message.walk():
        try:
            type = part.get_content_type()
            if type.startswith('multipart/'):
                continue
            elif type == 'text/plain':
                body = part.get_payload(decode=True)
                body = body.decode(part.get_content_charset())
                taskargs.update(parse_recipe_body(body))
            elif type.startswith('image/'):
                image_part = part
        except SubmitError, e:
            errors.append(e.message)
            
    if errors:
        send_error_mail(from_address, '\n'.join(errors))
        sys.exit(0)
        
    if image_part:
        taskargs['photo_path'] = save_image_file(image_part, 
                                                 taskargs['user_id'])
        
    task = SubmitRecipeTask(taskargs)
    get_taskqueue().send_task(task, queue_name="recipebook.recipe")
    
if __name__ == '__main__':
    main()
    
