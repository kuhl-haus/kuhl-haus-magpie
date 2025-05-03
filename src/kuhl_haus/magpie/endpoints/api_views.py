from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList
from kuhl_haus.magpie.endpoints.serializers import EndpointModelSerializer, DnsResolverSerializer, DnsResolverListSerializer


class EndpointModelViewSet(viewsets.ModelViewSet):
    queryset = EndpointModel.objects.all()
    serializer_class = EndpointModelSerializer

    @action(detail=True, methods=['get'])
    def health_check(self, request, pk=None):
        endpoint = self.get_object()
        # Simulate a health check (in a real app, you'd actually check the endpoint)
        health_status = {
            'status': 'healthy' if not endpoint.ignore else 'ignored',
            'mnemonic': endpoint.mnemonic,
            'url': f"{endpoint.scheme}://{endpoint.hostname}:{endpoint.port}{endpoint.path}"
        }
        return Response(health_status)


class DnsResolverViewSet(viewsets.ModelViewSet):
    queryset = DnsResolver.objects.all()
    serializer_class = DnsResolverSerializer


class DnsResolverListViewSet(viewsets.ModelViewSet):
    queryset = DnsResolverList.objects.all()
    serializer_class = DnsResolverListSerializer

    @action(detail=True, methods=['get'])
    def endpoints(self, request, pk=None):
        resolver_list = self.get_object()
        endpoints = resolver_list.endpoints.all()
        serializer = EndpointModelSerializer(endpoints, many=True)
        return Response(serializer.data)