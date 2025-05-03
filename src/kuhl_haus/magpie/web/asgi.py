# kuhl_haus/magpie/web/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhl_haus.magpie.web.settings')
application = get_asgi_application()
