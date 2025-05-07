from rest_framework import viewsets

from kuhl_haus.magpie.canary.models import CarbonClientConfig, ScriptConfig
from kuhl_haus.magpie.canary.serializers import CarbonClientConfigSerializer, ScriptConfigSerializer


class CarbonConfigViewSet(viewsets.ModelViewSet):
    queryset = CarbonClientConfig.objects.all()
    serializer_class = CarbonClientConfigSerializer


class ScriptConfigViewSet(viewsets.ModelViewSet):
    queryset = ScriptConfig.objects.all()
    serializer_class = ScriptConfigSerializer
