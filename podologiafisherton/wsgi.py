"""
WSGI config for corpuskinesio project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

# Añade el path de tu proyecto
path = os.path.expanduser('~/podologiafishertonhc')
if path not in sys.path:
    sys.path.insert(0, path)

# Establece el módulo de configuración de Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'podologiafisherton.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()