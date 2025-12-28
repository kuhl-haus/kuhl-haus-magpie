
def version_info(request):
    """
    Add version information to the template context
    """
    from os import environ
    from django.core.cache import cache

    result = cache.get('version_info')
    if result is None:
        result = {
            'version_info': {
                'image_version': environ.get('IMAGE_VERSION'),
                'container_image': environ.get('CONTAINER_IMAGE'),
            }
        }
        cache.set('version_info', result, 300)
    return result


def domain_info(request):
    from os import environ
    from django.core.cache import cache

    result = cache.get('domain_info')
    if result is None:
        result = {
            'MAGPIE_DOMAIN': environ.get('MAGPIE_DOMAIN'),
            'FLOWER_DOMAIN': environ.get('FLOWER_DOMAIN'),
        }
        cache.set('domain_info', result, 300)
    return result

