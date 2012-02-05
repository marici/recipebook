# coding: utf-8
import os

BASE_PATH = os.path.abspath(os.path.split(__file__)[0])

DEBUG = False
MAINTENANCE_BEGIN = u"3/6 (金) 10:00"
MAINTENANCE_END = u"13:00"

TIME_ZONE = 'Asia/Tokyo'
LANGUAGE_CODE = 'ja'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = '%s/site_media/' % BASE_PATH
MEDIA_URL = '/site_media/'
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = 'YOUR_SECRET_KEY'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)
ROOT_URLCONF = 'recipebook.maintenanceurls'
TEMPLATE_DIRS = (
    os.path.join(BASE_PATH, "templates"),
)
INSTALLED_APPS = (
    'recipebook.recipes',
)
