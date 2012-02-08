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
import os, logging
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import Image, ImageFilter
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FileField, ImageField, ImageFieldFile

log = logging.getLogger(__name__)

def get_names(field_name):
    s3_field_name = "%s_s3" % field_name
    s3_flag_name = "%s_sync" % s3_field_name
    sync_prop_name = "sync_%s" % field_name
    return s3_field_name, s3_flag_name, sync_prop_name


class ResizedImageFieldFile(ImageFieldFile):

    @classmethod
    def resize_content(cls, content, max_width=None, max_height=None):
        try:
            img = Image.open(content)
            width, height = img.size
            width = int(max_width or width)
            height = int(max_height or height)
            img.thumbnail((width, height), Image.ANTIALIAS)
            try:
                img.filter(ImageFilter.DETAIL)
            except ValueError, e:
                pass
            sio = StringIO()
            img.save(sio, img.format, quality=95)
            sio.seek(0)
            content.close()
            return InMemoryUploadedFile(sio, None, None, None, None, None)
        except Exception, e:
            log.warn("An error occured when resizing image. %s" % e)
            return content

    def save(self, name, content, save=True):
        content = self.resize_content(content, self.field.max_width,
                                      self.field.max_height)
        super(ResizedImageFieldFile, self).save(name, content, save)


class ResizedImageField(ImageField):
    attr_class = ResizedImageFieldFile

    def __init__(self, verbose_name=None, name=None,
                 max_width=None, max_height=None, **kwargs):
        self.max_width = max_width
        self.max_height = max_height
        super(ResizedImageField, self).__init__(verbose_name, name, **kwargs)


class S3SyncField(object):

    @classmethod
    def send_to_s3(cls, model, field_name, s3_name, s3_flag_name, delete=False):
        attr = getattr(model, field_name)
        s3_attr = getattr(model, s3_name)

        try:
            f = open(attr.path, "rb")
        except ValueError, e:
            return
        image = f.read()
        f.close()
        aws_file = s3_attr.storage.open(attr.name, "wb")
        aws_file.write(image)
        aws_file.close()
        
        model.__dict__[s3_name] = attr.name
        model.__dict__[s3_flag_name] = True
        model.save()
        
        if delete:
            os.remove(attr.path)


class S3SyncFileField(S3SyncField, FileField):
    pass


class S3SyncImageField(S3SyncField, ImageField):
    pass


class S3SyncResizedImageField(S3SyncField, ResizedImageField):
    pass
