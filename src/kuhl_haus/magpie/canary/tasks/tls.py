import ssl
import time
from datetime import datetime
from logging import Logger

import OpenSSL

from kuhl_haus.magpie.endpoints.models import EndpointModel
from kuhl_haus.magpie.metrics.data.metrics import Metrics


def invoke_tls_check(ep: EndpointModel, metrics: Metrics, logger: Logger):
    try:
        metrics.set_counter('requests', 1)
        start_time = time.perf_counter_ns()
        days_until_expiration = get_tls_cert_expiration_days(ep.hostname, ep.port)
        response_time = time.perf_counter_ns() - start_time
        metrics.attributes['response_time'] = int(response_time)
        metrics.attributes['response_time_ms'] = int(response_time // 1_000_000)
        metrics.set_counter('responses', 1)
        metrics.attributes["days_until_expiration"] = days_until_expiration
        metrics.attributes["expires_today"] = days_until_expiration <= 1
        metrics.attributes["is_valid"] = days_until_expiration > 0
    except Exception as e:
        metrics.set_counter('exceptions', 1)
        metrics.attributes['exception'] = repr(e)
        logger.exception(msg=f"unhandled exception processing {ep.hostname}:{ep.port}", exc_info=e)


def get_tls_cert_expiration_days(hostname: str, port: int) -> int:
    raw_cert = ssl.get_server_certificate((hostname, port))
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, raw_cert.encode())
    expiration_time = time.mktime(datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%S%fZ').timetuple())
    current_time = time.mktime(datetime.now().timetuple())
    return int(expiration_time - current_time) // 60 // 60 // 24
