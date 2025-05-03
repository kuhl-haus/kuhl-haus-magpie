from rest_framework import serializers
from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList


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
            'mnemonic', 'hostname', 'scheme', 'port', 'path', 'query', 'fragment',
            'healthy_status_code', 'json_response', 'status_key', 'healthy_status',
            'version_key', 'connect_timeout', 'read_timeout', 'ignore'
        ]
