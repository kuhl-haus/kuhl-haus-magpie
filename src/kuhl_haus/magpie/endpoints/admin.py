from django.contrib import admin
from kuhl_haus.magpie.endpoints.models import (
    EndpointModel,
    DnsResolver,
    DnsResolverList,
    CarbonClientConfig,
    ScriptConfig
)


@admin.register(CarbonClientConfig)
class CarbonClientConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'server_ip', 'pickle_port')
    search_fields = ('name', 'server_ip', 'pickle_port')


@admin.register(ScriptConfig)
class ScriptConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'application_name', 'log_level', 'namespace_root', 'metric_namespace', 'delay', 'count')
    list_filter = ('application_name', 'log_level', 'namespace_root', 'metric_namespace', 'delay', 'count')
    search_fields = ('name', 'application_name', 'namespace_root', 'metric_namespace')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'application_name',),
        }),
        ('Logging Parameters', {
            'fields': ('log_level',),
        }),
        ('Metrics Parameters', {
            'fields': ('namespace_root', 'metric_namespace',),
        }),
        ('Runtime Parameters', {
            'fields': ('delay', 'count'),
        }),
    )


@admin.register(DnsResolver)
class DnsResolverAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address')
    search_fields = ('name', 'ip_address')


@admin.register(DnsResolverList)
class DnsResolverListAdmin(admin.ModelAdmin):
    filter_horizontal = ('resolvers',)


@admin.register(EndpointModel)
class EndpointModelAdmin(admin.ModelAdmin):
    list_display = ('mnemonic', 'hostname', 'ignore', 'tls_check', 'dns_check', 'health_check',)
    list_filter = ('mnemonic', 'hostname', 'ignore', 'tls_check', 'dns_check', 'health_check',)
    search_fields = ('mnemonic', 'hostname')
    fieldsets = (
        ('Basic Information', {
            'fields': ('mnemonic', 'hostname',)
        }),
        ('Checks', {
            'fields': ('ignore', 'tls_check', 'dns_check', 'health_check',)
        }),
        ('Health Check Configuration', {
            'fields': (
                'scheme', 'port', 'path', 'verb', 'query', 'fragment'
            )
        }),
        ('Post Parameters', {
            'fields': ('body',),
        }),
        ('Response Settings', {
            'fields': ('healthy_status_code', 'response_format')
        }),
        ('JSON Response Settings', {
            'fields': ('status_key', 'healthy_status', 'version_key')
        }),
        ('Timeout Settings', {
            'fields': ('connect_timeout', 'read_timeout')
        }),
        ('Additional Settings', {
            'fields': ('dns_resolver_list',)
        }),
    )
