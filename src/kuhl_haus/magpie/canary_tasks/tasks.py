import logging
from typing import List

from django.core.exceptions import ObjectDoesNotExist

from kuhl_haus.magpie.canary.tasks.dns_check import query_dns
from kuhl_haus.magpie.canary.tasks.http_health_check import invoke_health_check
from kuhl_haus.magpie.canary.tasks.tls import invoke_tls_check
from kuhl_haus.magpie.endpoints.models import EndpointModel, ScriptConfig
from kuhl_haus.magpie.metrics.clients.carbon_poster import CarbonPoster
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.web.celery_app import app

logger = logging.getLogger(__name__)


@app.task
def http_health_check(script_config_name: str = "http_health_check"):
    try:
        script_config = ScriptConfig.objects.get(name__iexact=script_config_name)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"{script_config_name} configuration not found in database"
            }
        }
    result_metadata = {
        "script_config": {
            "name": script_config.name,
            "application_name": script_config.application_name,
            "log_level": script_config.log_level,
            "carbon_metrics_enabled": script_config.carbon_metrics_enabled,
            "carbon_server_ip": script_config.carbon_server_ip,
            "carbon_pickle_port": script_config.carbon_pickle_port,
            "namespace_root": script_config.namespace_root,
            "metric_namespace": script_config.metric_namespace,
        },
    }
    try:
        endpoints = EndpointModel.objects.filter(health_check=True, ignore=False)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"EndpointModel not found in database"
            }
        }
    try:
        carbon_poster: CarbonPoster = CarbonPoster(
            server_ip=script_config.carbon_server_ip,
            pickle_port=script_config.carbon_pickle_port,
        )
    except Exception as e:
        return {
            "status": "failed",
            "results": {
                "message": f"Unhandled exception instantiating CarbonPoster: {e}"
            }
        }
    metrics: List[tuple] = []
    for ep in endpoints:
        if ep.ignore:
            logger.info(f"Skipping {ep.mnemonic}")
            continue
        try:
            m: Metrics = Metrics(
                name=script_config.application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{ep.environment}",
                hostname=ep.hostname,
                counters={
                    'exceptions': 0,
                    'requests': 1,
                    'responses': 0,
                },
            )
            invoke_health_check(ep=ep, metrics=m, logger=logger)
            metrics.extend(m.carbon)
        except Exception as e:
            logger.exception(
                msg=f"Unhandled exception testing mnemonic:{ep.mnemonic}",
                exc_info=e
            )
    try:
        if metrics:
            # Batch size configuration
            batch_size = 64  # You can adjust this value based on your needs

            # Split metrics into batches
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                carbon_poster.post_metrics(metrics=batch)
                logger.info(f"Successfully posted batch of {len(batch)} metrics to Carbon.")

            message = f"Successfully posted all {len(metrics)} metrics to Carbon in {(len(metrics) + batch_size - 1) // batch_size} batches."
            logger.info(message)

            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": message
                }
            }
        else:
            logger.warning(f"No metrics posted to Carbon because no metrics are available.")
            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": "No metrics posted to Carbon because no metrics are available."
                }
            }
    except Exception as e:
        logger.exception(
            msg=f"Unhandled exception posting metrics to Carbon. Metric count:{len(metrics)}",
            exc_info=e
        )
        raise


@app.task
def tls_check(script_config_name: str = "tls_check"):
    try:
        script_config = ScriptConfig.objects.get(name__iexact=script_config_name)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"{script_config_name} configuration not found in database"
            }
        }
    result_metadata = {
        "script_config": {
            "name": script_config.name,
            "application_name": script_config.application_name,
            "log_level": script_config.log_level,
            "carbon_metrics_enabled": script_config.carbon_metrics_enabled,
            "carbon_server_ip": script_config.carbon_server_ip,
            "carbon_pickle_port": script_config.carbon_pickle_port,
            "namespace_root": script_config.namespace_root,
            "metric_namespace": script_config.metric_namespace,
        },
    }
    try:
        endpoints = EndpointModel.objects.filter(tls_check=True, ignore=False)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"EndpointModel not found in database"
            }
        }
    try:
        carbon_poster: CarbonPoster = CarbonPoster(
            server_ip=script_config.carbon_server_ip,
            pickle_port=script_config.carbon_pickle_port,
        )
    except Exception as e:
        return {
            "status": "failed",
            "results": {
                "message": f"Unhandled exception instantiating CarbonPoster: {e}"
            }
        }
    metrics: List[tuple] = []
    for ep in endpoints:
        if ep.ignore:
            logger.info(f"Skipping {ep.mnemonic}")
            continue
        try:
            m: Metrics = Metrics(
                name=script_config.application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{ep.environment}",
                hostname=ep.hostname,
                counters={
                    'exceptions': 0,
                    'requests': 1,
                    'responses': 0,
                },
            )
            invoke_tls_check(ep=ep, metrics=m, logger=logger)
            metrics.extend(m.carbon)
        except Exception as e:
            logger.exception(
                msg=f"Unhandled exception testing mnemonic:{ep.mnemonic}",
                exc_info=e
            )
    try:
        if metrics:
            # Batch size configuration
            batch_size = 64  # You can adjust this value based on your needs

            # Split metrics into batches
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                carbon_poster.post_metrics(metrics=batch)
                logger.info(f"Successfully posted batch of {len(batch)} metrics to Carbon.")

            message = f"Successfully posted all {len(metrics)} metrics to Carbon in {(len(metrics) + batch_size - 1) // batch_size} batches."
            logger.info(message)

            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": message
                }
            }
        else:
            logger.warning(f"No metrics posted to Carbon because no metrics are available.")
            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": "No metrics posted to Carbon because no metrics are available."
                }
            }
    except Exception as e:
        logger.exception(
            msg=f"Unhandled exception posting metrics to Carbon. Metric count:{len(metrics)}",
            exc_info=e
        )
        raise


@app.task
def dns_check(script_config_name: str = "dns_check"):
    try:
        script_config = ScriptConfig.objects.get(name__iexact=script_config_name)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"{script_config_name} configuration not found in database"
            }
        }
    result_metadata = {
        "script_config": {
            "name": script_config.name,
            "application_name": script_config.application_name,
            "log_level": script_config.log_level,
            "carbon_metrics_enabled": script_config.carbon_metrics_enabled,
            "carbon_server_ip": script_config.carbon_server_ip,
            "carbon_pickle_port": script_config.carbon_pickle_port,
            "namespace_root": script_config.namespace_root,
            "metric_namespace": script_config.metric_namespace,
        },
    }
    try:
        endpoints = EndpointModel.objects.filter(dns_check=True, ignore=False, dns_resolver_list__isnull=False)
    except ObjectDoesNotExist:
        return {
            "status": "failed",
            "results": {
                "message": f"EndpointModel not found in database"
            }
        }
    try:
        carbon_poster: CarbonPoster = CarbonPoster(
            server_ip=script_config.carbon_server_ip,
            pickle_port=script_config.carbon_pickle_port,
        )
    except Exception as e:
        return {
            "status": "failed",
            "results": {
                "message": f"Unhandled exception instantiating CarbonPoster: {e}"
            }
        }
    metrics: List[tuple] = []
    for ep in endpoints:
        if ep.ignore:
            logger.info(f"Skipping {ep.mnemonic}")
            continue
        try:
            m: Metrics = Metrics(
                name=script_config.application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{ep.environment}",
                hostname=ep.hostname,
                counters={
                    'exceptions': 0,
                    'requests': 1,
                    'responses': 0,
                },
            )
            query_dns(resolvers=ep.dns_resolver_list, ep=ep, metrics=m, logger=logger)
            metrics.extend(m.carbon)
        except Exception as e:
            logger.exception(
                msg=f"Unhandled exception testing mnemonic:{ep.mnemonic}",
                exc_info=e
            )
    try:
        if metrics:
            # Batch size configuration
            batch_size = 64  # You can adjust this value based on your needs

            # Split metrics into batches
            for i in range(0, len(metrics), batch_size):
                batch = metrics[i:i + batch_size]
                carbon_poster.post_metrics(metrics=batch)
                logger.info(f"Successfully posted batch of {len(batch)} metrics to Carbon.")

            message = f"Successfully posted all {len(metrics)} metrics to Carbon in {(len(metrics) + batch_size - 1) // batch_size} batches."
            logger.info(message)

            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": message
                }
            }
        else:
            logger.warning(f"No metrics posted to Carbon because no metrics are available.")
            return {
                "status": "success",
                "metadata": result_metadata,
                "results": {
                    "message": "No metrics posted to Carbon because no metrics are available."
                }
            }
    except Exception as e:
        logger.exception(
            msg=f"Unhandled exception posting metrics to Carbon. Metric count:{len(metrics)}",
            exc_info=e
        )
        raise
