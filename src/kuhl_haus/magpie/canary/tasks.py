import logging
import os

from django.core.exceptions import ObjectDoesNotExist
from kuhl_haus.canary.scripts.canary import Canary
from kuhl_haus.metrics.recorders.graphite_logger import GraphiteLogger, GraphiteLoggerOptions

from kuhl_haus.magpie.canary.models import CarbonClientConfig, ScriptConfig
from kuhl_haus.magpie.web.celery_app import app

CONFIG_API = os.environ.get("CONFIG_API")


logger = logging.getLogger(__name__)


@app.task
def canary(carbon_client_name: str = "default", application_name: str = "canary"):
    try:
        carbon_configs = CarbonClientConfig.objects.filter(name__iexact=carbon_client_name)
        carbon_config = list(carbon_configs).pop()
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": "Carbon client configuration not found in database"
            }
        }

    # Get the ScriptConfig from Django ORM by 'name'
    try:
        script_configs = ScriptConfig.objects.filter(application_name__iexact=application_name)
        script_config = list(script_configs).pop()
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": "canary configuration not found in database"
            }
        }
    result_metadata = {
        "application_name": script_config.application_name,
        "script_config": script_config.to_dict(),
        "carbon_config": carbon_config.to_dict(),
    }
    try:
        graphite_logger = GraphiteLogger(GraphiteLoggerOptions(
            application_name=application_name,
            log_level=script_config.log_level,
            carbon_config={"server_ip": carbon_config.server_ip, "pickle_port": carbon_config.pickle_port},
            thread_pool_size=10,
            namespace_root=script_config.namespace_root,
            metric_namespace=script_config.application_name,
            pod_name=os.environ.get("POD_NAME"),
        ))
    except Exception as e:
        return {
            "status": "failed",
            "metadata": result_metadata,
            "results": {
                "message": "Unable to initialize GraphiteLogger.",
                "error": str(e)
            }
        }
    try:
        Canary(recorder=graphite_logger, delay=script_config.delay, count=script_config.count)
    except Exception as e:
        return {
            "status": "failed",
            "metadata": result_metadata,
            "results": {
                "message": "Unhandled exception raised while running canary script.",
                "error": str(e)
            }
        }
    return {
        "status": "success",
        "metadata": result_metadata,
        "results": {
            "message": "Canary script started successfully."
        }
    }
