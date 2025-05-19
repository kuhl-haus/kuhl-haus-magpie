import logging
import os
from typing import List

from celery import shared_task

from django.core.exceptions import ObjectDoesNotExist
from kuhl_haus.canary.scripts.canary import Canary
from kuhl_haus.canary.tasks.dns_check import query_dns
from kuhl_haus.metrics.recorders.graphite_logger import GraphiteLogger, GraphiteLoggerOptions
from kuhl_haus.metrics.clients.carbon_poster import CarbonPoster
from kuhl_haus.metrics.data.metrics import Metrics

from kuhl_haus.magpie.canary.models import CarbonClientConfig, ScriptConfig
from kuhl_haus.canary.tasks.http_health_check import invoke_health_check
from kuhl_haus.canary.tasks.tls import invoke_tls_check
from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolver, DnsResolverList
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
            "metric_namespace": script_config.metric_namespace,
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
            metric_namespace=script_config.metric_namespace,
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


@shared_task
def http_health_check(carbon_client_name: str = "default", application_name: str = "health"):
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
            "metric_namespace": script_config.metric_namespace,
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
            server_ip=carbon_config.server_ip,
            pickle_port=carbon_config.pickle_port
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
                name=application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{script_config.metric_namespace}",
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


@shared_task
def tls_check(carbon_client_name: str = "default", application_name: str = "tls"):
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
            "metric_namespace": script_config.metric_namespace,
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
            server_ip=carbon_config.server_ip,
            pickle_port=carbon_config.pickle_port
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
                name=application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{script_config.metric_namespace}",
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


@shared_task
def dns_check(carbon_client_name: str = "default", application_name: str = "dns"):
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
            "metric_namespace": script_config.metric_namespace,
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
            server_ip=carbon_config.server_ip,
            pickle_port=carbon_config.pickle_port
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
                name=application_name,
                mnemonic=ep.mnemonic,
                namespace=f"{script_config.namespace_root}.{script_config.metric_namespace}",
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

