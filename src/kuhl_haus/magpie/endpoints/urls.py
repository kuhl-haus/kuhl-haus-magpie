from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kuhl_haus.magpie.endpoints import api_views

router = DefaultRouter()
router.register(r'api/endpoints', api_views.EndpointModelViewSet)
router.register(r'api/resolvers', api_views.DnsResolverViewSet)
router.register(r'api/resolver-lists', api_views.DnsResolverListViewSet)
router.register(r'api/scripts', api_views.ScriptConfigViewSet)


urlpatterns = [
    # API URLs
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls')),
]
