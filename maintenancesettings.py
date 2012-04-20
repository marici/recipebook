# -*- coding: utf-8 -*-
import os

BASE_PATH = os.path.dirname(__file__)

DEBUG = True
MAINTENANCE_BEGIN = u'3/6 (金) 10:00'
MAINTENANCE_END = u'13:00'

TIME_ZONE = 'Asia/Tokyo'
LANGUAGE_CODE = 'ja'
SITE_ID = 1
USE_I18N = True
MEDIA_ROOT = os.path.join(BASE_PATH, 'site_media/')
MEDIA_URL = '/site_media/'
ADMIN_MEDIA_PREFIX = '/media/'
SECRET_KEY = 'YOUR_SECRET_KEY'
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)
ROOT_URLCONF = 'recipebook.maintenanceurls'
TEMPLATE_DIRS = (
    os.path.join(BASE_PATH, 'templates'),
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'recipes',
)
