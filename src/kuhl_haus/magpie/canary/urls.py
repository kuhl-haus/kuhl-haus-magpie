from django.urls import path, include
from rest_framework.routers import DefaultRouter
from kuhl_haus.magpie.canary import views

router = DefaultRouter()
router.register(r'api/carbon-configs', views.CarbonConfigViewSet)
router.register(r'api/scripts', views.ScriptConfigViewSet)


urlpatterns = [
    # API URLs
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls')),
]
