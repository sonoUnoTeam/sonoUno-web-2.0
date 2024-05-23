"""
WSGI config for sonounoweb project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

#path a donde esta el manage.py de nuestro proyecto Django
path = '/home/jcasado/webapp/sonoUno-web-2.0/sonounoweb'
if path not in sys.path:
    sys.path.append(path)

#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sonounoweb.settings')
#Para varias instancias corriendo
os.environ['DJANGO_SETTINGS_MODULE'] = 'sonounoweb.settings'

#Prevenir UnicodeEncodeError
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')

from dotenv import load_dotenv
project_floder = os.path.expanduser('~/sonounoweb')
load_dotenv(os.path.join(project_floder, '.env'))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
