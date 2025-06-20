import os
import sys
from importlib.metadata import version

from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhl_haus.magpie.web.settings')
IMAGE_VERSION = os.environ.get('IMAGE_VERSION', 'Unknown')
CONTAINER_IMAGE = os.environ.get('CONTAINER_IMAGE', 'Unknown')

try:
    __version__ = version("kuhl-haus.magpie")
except Exception as e:
    print(f"Error determining version: {repr(e)}", file=sys.stderr)
    __version__ = "Unknown"


@require_http_methods(["GET"])
@csrf_exempt
@never_cache
def http_health(request: HttpRequest) -> HttpResponse:
    """
    Simple health check endpoint for Kubernetes liveness probes.
    Returns plain text 'OK' with a status code of 200.
    """
    return HttpResponse("OK", content_type="text/plain")


@require_http_methods(["GET"])
@csrf_exempt
@never_cache
def json_health(request: HttpRequest) -> JsonResponse:
    """
    Detailed health check endpoint returns JSON with version information for deployment verification.
    """
    return JsonResponse({
        "status": "OK",
        "version": __version__,
        "image_version": IMAGE_VERSION,
        "container_image": CONTAINER_IMAGE
    })
