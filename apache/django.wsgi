import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'recipebook.prodsettings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
