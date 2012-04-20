# Django settings for recipebook project.

import os
BASE_PATH = os.path.abspath(os.path.split(__file__)[0])

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
#    ('username', 'mailaddress'),
)

MANAGERS = ADMINS

# Settings for database
DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'data.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

CACHE_BACKEND = 'dummy:///'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Tokyo'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ja'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: '/home/media/media.lawrence.com/'
MEDIA_ROOT = '%s/site_media/' % BASE_PATH

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: 'http://media.lawrence.com', 'http://example.com/media/'
MEDIA_URL = '/site_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: 'http://foo.com/media/', '/media/'.
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'YOUR_SECRET_KEY'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'maricilib.django.core.context_processors.csrf',
    'maricilib.django.core.context_processors.current_site',
    'maricilib.django.core.context_processors.settings',
    'recipes.context_processors.side1',
    'maricilib.django.apps.feedback.context_processors.form',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'recipebook.urls'

TEMPLATE_DIRS = (
    # Put strings here, like '/home/html/django_templates' or 'C:/www/django/templates'.
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',
    'maricilib.django.apps.sitenews',
    'maricilib.django.apps.documents',
    'maricilib.django.apps.search',
    'maricilib.django.apps.daily',
    'maricilib.django.apps.taskqueue',
    'maricilib.django.apps.feedback',
    'recipes',
)

LOGIN_REDIRECT_URL = '/home/'

AUTH_PROFILE_MODULE = 'recipes.UserProfile'

COPYRIGHT = u'&copy; 2009 recipebook.jp'

EMAIL_FROM = ''

USE_AWS = False
SEARCH_USE_SOLR = False

QUEUE_BACKEND = 'immediate'
QUEUENAME_EMAIL = 'recipebook.email'
QUEUENAME_SENDS3 = 'recipebook.s3'
QUEUENAME_RECIPE = 'recipebook.recipe'
TASKQUEUE_USE_SIGNAL = True

