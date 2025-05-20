import json
from logging import Logger

import requests.exceptions
import time
from requests import get, Response

from kuhl_haus.magpie.endpoints.models import EndpointModel
from kuhl_haus.magpie.metrics.data.metrics import Metrics


def invoke_health_check(ep: EndpointModel, metrics: Metrics, logger: Logger):
    try:
        metrics.set_counter('requests', 1)
        start_time = time.perf_counter_ns()
        response = get(url=ep.url, timeout=(ep.connect_timeout, ep.read_timeout))
        response_time = time.perf_counter_ns() - start_time
        metrics.attributes['response_time'] = int(response_time)
        metrics.attributes['response_time_ms'] = int(response_time // 1_000_000)
        metrics.attributes['status_code'] = response.status_code
        metrics.attributes['text'] = response.text

        if ep.response_format == "json":
            handle_json_response(response=response, ep=ep, metrics=metrics)
        elif response.status_code == ep.healthy_status_code:
            metrics.set_counter('responses', 1)
        else:
            metrics.set_counter('errors', 1)
        if "X-Request-Time" in response.headers:
            metrics.attributes['request_time'] = response.headers["X-Request-Time"]
        if "X-Request-Time-MS" in response.headers:
            metrics.attributes['request_time_ms'] = response.headers["X-Request-Time-MS"]
        if "X-Metrics-Time" in response.headers:
            metrics.attributes['metrics_time'] = response.headers["X-Metrics-Time"]
        if "X-Metrics-Time-MS" in response.headers:
            metrics.attributes['metrics_time_ms'] = response.headers["X-Metrics-Time-MS"]

    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        logger.exception(
            msg=f"The request timed out before the server responded {ep.hostname}:{ep.port}", exc_info=e)
        metrics.set_counter('exceptions', 1)
        metrics.attributes['exception'] = f"The request timed out before the server responded: {e}"
        metrics.attributes['response_time'] = int(ep.connect_timeout + ep.read_timeout)
        metrics.attributes['response_time_ms'] = int((ep.connect_timeout + ep.read_timeout) // 1_000_000)
    except Exception as e:
        logger.exception(msg=f"unhandled exception processing {metrics.mnemonic} on {ep.hostname}", exc_info=e)
        metrics.attributes['exception'] = f"Unhandled exception thrown: {e}"
        metrics.set_counter('exceptions', 1)


def handle_json_response(response: Response, ep: EndpointModel, metrics: Metrics):
    if response.text is not None:
        json_response = json.loads(response.text)
        if ep.status_key in json_response and json_response[ep.status_key] == ep.healthy_status:
            metrics.set_counter('responses', 1)
        else:
            metrics.set_counter('errors', 1)
        if ep.version_key in json_response:
            api_version = metrics.version_to_float(json_response[ep.version_key])
            metrics.attributes['version'] = api_version
    else:
        metrics.set_counter('errors', 1)
