from logging import Logger

import time

import dns.query
from dns.message import make_query

from kuhl_haus.magpie.endpoints.models import EndpointModel, DnsResolverList
from kuhl_haus.magpie.metrics.data.metrics import Metrics


def query_dns(resolvers: DnsResolverList, ep: EndpointModel, metrics: Metrics, logger: Logger):
    if not resolvers:
        return
    resolver_list = resolvers.resolvers.get()
    if not isinstance(resolver_list, list):
        resolver_list = [resolver_list]
    for resolver in resolver_list:
        try:
            metrics.set_counter('requests', 1)
            start_time = time.perf_counter_ns()
            response: dns.message.Message = dns_query(resolver.ip_address, ep.hostname, "A", use_tcp=False)
            response_time = time.perf_counter_ns() - start_time
            metrics.attributes['response_time'] = int(response_time)
            metrics.attributes['response_time_ms'] = int(response_time // 1_000_000)
            metrics.set_counter('responses', 1)
            metrics.attributes['truncated'] = int((dns.flags.TC & response.flags) > 0)
            metrics.attributes['rcode'] = dns.rcode.to_text(response.rcode())
            metrics.attributes['result'] = response.to_text()
            return  # return on first successful DNS response
        except (dns.query.BadResponse, dns.query.UnexpectedSource) as e:
            metrics.attributes['exception'] = repr(e)
            metrics.set_counter('errors', 1)
            metrics.attributes['rcode'] = 'ERROR'
            logger.exception(msg=f"Invalid DNS response for {ep.hostname} from {resolver.ip_address}", exc_info=e)
        except dns.exception.Timeout as e:
            metrics.attributes['exception'] = repr(e)
            metrics.set_counter('errors', 1)
            metrics.attributes['rcode'] = 'TIMEOUT'
            logger.exception(msg=f"DNS timeout querying {ep.hostname} using {resolver.ip_address}", exc_info=e)
        except Exception as e:
            metrics.attributes['exception'] = repr(e)
            metrics.set_counter('exceptions', 1)
            metrics.attributes['rcode'] = 'FATAL'
            logger.exception(msg=f"unhandled exception querying DNS for {ep.hostname} using {resolver.ip_address}", exc_info=e)


def dns_query(ip_address, query_name, rr_type, use_tcp=True) -> dns.message.Message:
    qname = dns.name.from_text(query_name)
    rd_type = dns.rdatatype.from_text(rr_type)
    if use_tcp:
        dns_message = make_query(qname=qname, rdtype=rd_type)
        return dns.query.tcp(dns_message, ip_address, timeout=1)
    else:
        dns_message = make_query(qname=qname, rdtype=rd_type, use_edns=True, ednsflags=0, payload=4096)
        return dns.query.udp(dns_message, ip_address, timeout=1)
