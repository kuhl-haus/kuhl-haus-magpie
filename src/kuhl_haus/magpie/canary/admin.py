from django.contrib import admin
from kuhl_haus.magpie.canary.models import CarbonClientConfig, ScriptConfig


@admin.register(CarbonClientConfig)
class CarbonClientConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'server_ip', 'pickle_port')
    search_fields = ('name', 'server_ip', 'pickle_port')


@admin.register(ScriptConfig)
class ScriptConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'application_name', 'log_level', 'namespace_root', 'delay', 'count')
    list_filter = ('application_name', 'log_level', 'namespace_root', 'delay', 'count')
    search_fields = ('name', 'application_name', 'namespace_root')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'application_name',),
        }),
        ('Logging Parameters', {
            'fields': ('log_level',),
        }),
        ('Metrics Parameters', {
            'fields': ('namespace_root',),
        }),
        ('Runtime Parameters', {
            'fields': ('delay', 'count'),
        }),
    )
