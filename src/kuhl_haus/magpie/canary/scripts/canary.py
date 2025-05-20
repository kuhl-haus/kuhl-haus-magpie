from typing import List

from kuhl_haus.magpie.canary.helpers.canary_configs import (
    get_endpoints,
    get_default_resolver_list,
)
from kuhl_haus.magpie.endpoints.models import DnsResolver, EndpointModel
from kuhl_haus.magpie.canary.scripts.script import Script
from kuhl_haus.magpie.canary.tasks.dns_check import query_dns
from kuhl_haus.magpie.canary.tasks.http_health_check import invoke_health_check
from kuhl_haus.magpie.canary.tasks.tls import invoke_tls_check


class Canary(Script):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def invoke(self):
        self.__invoke_endpoint_checks()

    def __invoke_endpoint_checks(self):
        endpoints = get_endpoints()
        resolvers = get_default_resolver_list()

        if not endpoints:
            self.recorder.logger.info(f"No endpoints found, exiting.")
            return
        for ep in endpoints:
            if ep.ignore:
                self.recorder.logger.info(f"Skipping {ep.mnemonic}")
                continue
            try:
                if resolvers and ep.dns_check:
                    self.__invoke_dns_check(ep=ep, resolvers=resolvers)
                if ep.tls_check:
                    self.__invoke_tls_check(ep=ep)
                if ep.health_check:
                    self.__invoke_health_check(ep=ep)
            except Exception as e:
                self.recorder.logger.exception(
                    msg=f"Unhandled exception testing mnemonic:{ep.mnemonic}",
                    exc_info=e
                )

    def __invoke_health_check(self, ep: EndpointModel):
        metrics = self.recorder.get_metrics(name="health", mnemonic=ep.mnemonic, hostname=ep.hostname)
        invoke_health_check(ep=ep, metrics=metrics, logger=self.recorder.logger)
        self.recorder.log_metrics(metrics)

    def __invoke_tls_check(self, ep: EndpointModel):
        metrics = self.recorder.get_metrics(name="tls", mnemonic=ep.mnemonic, hostname=ep.hostname)
        invoke_tls_check(ep=ep, metrics=metrics, logger=self.recorder.logger)
        self.recorder.log_metrics(metrics)

    def __invoke_dns_check(self, ep: EndpointModel, resolvers: List[DnsResolver]):
        metrics = self.recorder.get_metrics(name="dns", mnemonic=ep.mnemonic, hostname=ep.hostname)
        query_dns(resolvers=resolvers, ep=ep, metrics=metrics, logger=self.recorder.logger)
        self.recorder.log_metrics(metrics)
