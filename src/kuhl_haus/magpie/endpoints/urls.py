from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from kuhl_haus.magpie.endpoints import views
from kuhl_haus.magpie.endpoints import api_views

router = DefaultRouter()
router.register(r'api/endpoints', api_views.EndpointModelViewSet)
router.register(r'api/resolvers', api_views.DnsResolverViewSet)
router.register(r'api/resolver-lists', api_views.DnsResolverListViewSet)


urlpatterns = [
    # Endpoint URLs
    path('', views.EndpointListView.as_view(), name='endpoint-list'),
    path('endpoint/<int:pk>/', views.EndpointDetailView.as_view(), name='endpoint-detail'),
    path('endpoint/new/', views.EndpointCreateView.as_view(), name='endpoint-create'),
    path('endpoint/<int:pk>/edit/', views.EndpointUpdateView.as_view(), name='endpoint-update'),
    path('endpoint/<int:pk>/delete/', views.EndpointDeleteView.as_view(), name='endpoint-delete'),

    # DNS Resolver URLs
    path('resolvers/', views.DnsResolverListView.as_view(), name='resolver-list'),
    path('resolver/<int:pk>/', views.DnsResolverDetailView.as_view(), name='resolver-detail'),
    path('resolver/new/', views.DnsResolverCreateView.as_view(), name='resolver-create'),
    path('resolver/<int:pk>/edit/', views.DnsResolverUpdateView.as_view(), name='resolver-update'),
    path('resolver/<int:pk>/delete/', views.DnsResolverDeleteView.as_view(), name='resolver-delete'),

    # DNS Resolver List URLs
    path('resolver-lists/', views.DnsResolverListListView.as_view(), name='resolver-list-list'),
    path('resolver-list/<int:pk>/', views.DnsResolverListDetailView.as_view(), name='resolver-list-detail'),
    path('resolver-list/new/', views.DnsResolverListCreateView.as_view(), name='resolver-list-create'),
    path('resolver-list/<int:pk>/edit/', views.DnsResolverListUpdateView.as_view(), name='resolver-list-update'),
    path('resolver-list/<int:pk>/delete/', views.DnsResolverListDeleteView.as_view(), name='resolver-list-delete'),

    # API URLs
    path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls')),
]
