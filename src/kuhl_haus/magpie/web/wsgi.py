# kuhl_haus/magpie/web/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhl_haus.magpie.web.settings')
application = get_wsgi_application()
