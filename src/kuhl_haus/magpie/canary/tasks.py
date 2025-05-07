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
        carbon_config = CarbonClientConfig.objects.get(name__iexact=carbon_client_name)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"Carbon client configuration {carbon_client_name} not found in database"
            }
        }

    try:
        script_config = ScriptConfig.objects.get(application_name__iexact=application_name)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"{application_name} configuration not found in database"
            }
        }
    result_metadata = {
        "script_config": {
            "name": script_config.name,
            "application_name": script_config.application_name,
            "log_level": script_config.log_level,
            "namespace_root": script_config.namespace_root,
            "delay": script_config.delay,
            "count": script_config.count,
        },
        "carbon_config": {
            "name": carbon_config.name,
            "server_ip": carbon_config.server_ip,
            "pickle_port": carbon_config.pickle_port,
        },
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
