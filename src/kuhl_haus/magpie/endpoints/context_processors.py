
def version_info(request):
    """
    Add version information to the template context
    """
    from django.conf import settings
    from django.core.cache import cache

    app_version = cache.get('app_version')
    if app_version is None:
        app_version = getattr(settings, 'APP_VERSION', "")
        if app_version:
            cache.set('app_version', app_version, 3600)

    container_version = cache.get('container_version')
    if container_version is None:
        container_version = getattr(settings, 'CONTAINER_VERSION', "")
        if container_version:
            cache.set('container_version', container_version, 3600)

    return {
        'version_info': {
            'app_version': app_version,
            'container_version': container_version,
        }
    }


def flower_domain(request):
    from django.conf import settings
    return {'FLOWER_DOMAIN': settings.FLOWER_DOMAIN}
