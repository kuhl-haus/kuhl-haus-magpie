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
    list_display = ('mnemonic', 'hostname', 'scheme', 'port', 'healthy_status_code', 'ignore')
    list_filter = ('scheme', 'json_response', 'ignore')
    search_fields = ('mnemonic', 'hostname')
    fieldsets = (
        ('Basic Information', {
            'fields': ('mnemonic', 'hostname', 'scheme', 'port', 'path')
        }),
        ('Query Parameters', {
            'fields': ('query', 'fragment'),
        }),
        ('Health Check Configuration', {
            'fields': ('healthy_status_code', 'json_response', 'status_key', 'healthy_status', 'version_key')
        }),
        ('Timeout Settings', {
            'fields': ('connect_timeout', 'read_timeout')
        }),
        ('Additional Settings', {
            'fields': ('ignore', 'dns_resolver_list')
        }),
    )
