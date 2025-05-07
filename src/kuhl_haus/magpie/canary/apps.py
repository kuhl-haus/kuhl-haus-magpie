from django.apps import AppConfig


class CanaryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kuhl_haus.magpie.canary'
    label = 'canary'
