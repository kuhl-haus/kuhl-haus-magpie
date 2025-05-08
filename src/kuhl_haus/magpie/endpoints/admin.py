from django.contrib import admin
from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList


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
            'fields': ('mnemonic', 'hostname', 'scheme', 'port', 'path', 'verb')
        }),
        ('Query Parameters', {
            'fields': ('query', 'fragment'),
        }),
        ('Post Parameters', {
            'fields': ('body',),
        }),
        ('Response Settings', {
            'fields': ('healthy_status_code', 'response_format',)
        }),
        ('Health Check Configuration', {
            'fields': (
                'ignore', 'tls_check', 'dns_check', 'health_check',
                'status_key', 'healthy_status', 'version_key'
            )
        }),
        ('Timeout Settings', {
            'fields': ('connect_timeout', 'read_timeout')
        }),
        ('Additional Settings', {
            'fields': ('dns_resolver_list',)
        }),
    )
