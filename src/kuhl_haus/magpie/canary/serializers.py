from rest_framework import serializers
from kuhl_haus.magpie.canary.models import CarbonClientConfig, ScriptConfig


class CarbonClientConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonClientConfig
        fields = ['name', 'server_ip', 'pickle_port']


class ScriptConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptConfig
        fields = [
            'name', 'application_name', 'log_level', 'namespace_root', 'delay', 'count'
        ]
