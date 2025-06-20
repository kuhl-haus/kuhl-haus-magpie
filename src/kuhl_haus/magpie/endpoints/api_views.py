from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from kuhl_haus.magpie.endpoints.models import (
    EndpointModel,
    DnsResolver,
    DnsResolverList,
    ScriptConfig
)
from kuhl_haus.magpie.endpoints.serializers import (
    EndpointModelSerializer,
    DnsResolverSerializer,
    DnsResolverListSerializer,
    ScriptConfigSerializer
)


class ScriptConfigViewSet(viewsets.ModelViewSet):
    queryset = ScriptConfig.objects.all()
    serializer_class = ScriptConfigSerializer


class EndpointModelViewSet(viewsets.ModelViewSet):
    queryset = EndpointModel.objects.all()
    serializer_class = EndpointModelSerializer


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
