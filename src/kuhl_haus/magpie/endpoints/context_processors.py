def flower_domain(request):
    from django.conf import settings
    return {'FLOWER_DOMAIN': settings.FLOWER_DOMAIN}
