# import json
from django import forms
from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList


class EndpointModelForm(forms.ModelForm):
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
            'dns_resolver_list'
        ]
        widgets = {
            'connect_timeout': forms.NumberInput(attrs={'step': '0.1'}),
            'read_timeout': forms.NumberInput(attrs={'step': '0.1'}),
            'body': forms.Textarea(attrs={'rows': 5}),
        }


class DnsResolverForm(forms.ModelForm):
    class Meta:
        model = DnsResolver
        fields = ['name', 'ip_address']


class DnsResolverListForm(forms.ModelForm):
    resolvers = forms.ModelMultipleChoiceField(
        queryset=DnsResolver.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = DnsResolverList
        fields = ['name', 'resolvers']
