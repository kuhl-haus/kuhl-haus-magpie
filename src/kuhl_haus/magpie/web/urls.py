# kuhl_haus/magpie/web/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

import kuhl_haus.magpie.web.health as health

schema_view = get_schema_view(
   openapi.Info(
      title="Endpoint Manager API",
      default_version='v1',
      description="API for managing endpoints and DNS resolvers",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    # Index page
    path('', TemplateView.as_view(template_name='index.html'), name='index'),

    # Health Check
    path(r'healthz', health.json_health, name='healthz'),
    path(r'health', health.http_health, name='health'),

    path('admin/', admin.site.urls),
    path('', include('kuhl_haus.magpie.endpoints.urls')),

    # Swagger
    # drf-yasg
    path('api-<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
