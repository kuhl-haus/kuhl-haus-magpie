from rest_framework import serializers
from kuhl_haus.magpie.endpoints.models import (
    EndpointModel,
    DnsResolver,
    DnsResolverList,
    CarbonClientConfig,
    ScriptConfig
)


class CarbonClientConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarbonClientConfig
        fields = ['name', 'server_ip', 'pickle_port']


class ScriptConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScriptConfig
        fields = [
            'name', 'application_name', 'log_level', 'namespace_root', 'metric_namespace', 'delay', 'count'
        ]


class DnsResolverSerializer(serializers.ModelSerializer):
    class Meta:
        model = DnsResolver
        fields = ['name', 'ip_address']


class DnsResolverListSerializer(serializers.ModelSerializer):
    resolvers = DnsResolverSerializer(many=True, read_only=True)

    class Meta:
        model = DnsResolverList
        fields = ['name', 'resolvers']


class EndpointModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EndpointModel
        fields = [
            'mnemonic',
            'hostname', 'scheme', 'port',
            'path', 'query', 'fragment',
            'verb', 'body',
            'healthy_status_code', 'response_format',
            'status_key', 'healthy_status', 'version_key',
            'connect_timeout', 'read_timeout',
            'ignore', 'tls_check', 'dns_check', 'health_check',
        ]
