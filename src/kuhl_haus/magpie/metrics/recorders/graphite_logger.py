from __future__ import annotations

import random
import threading
from dataclasses import dataclass
from logging import Logger
from typing import Optional, Dict, Any

import time

from kuhl_haus.magpie.metrics.clients.carbon_poster import CarbonPoster
from kuhl_haus.magpie.metrics.data.metrics import Metrics
from kuhl_haus.magpie.metrics.env import (
    METRIC_NAMESPACE,
    NAMESPACE_ROOT,
    THREAD_POOL_SIZE,
)
from kuhl_haus.magpie.metrics.factories.logs import get_logger
from kuhl_haus.magpie.metrics.tasks.thread_pool import ThreadPool


@dataclass
class GraphiteLoggerOptions:
    application_name: str
    log_level: str
    carbon_config: Dict[str, Any]
    thread_pool_size: Optional[int] = THREAD_POOL_SIZE
    log_directory: Optional[str] = None
    namespace_root: Optional[str] = NAMESPACE_ROOT
    metric_namespace: Optional[str] = METRIC_NAMESPACE
    pod_name: Optional[str] = None


class GraphiteLogger:
    logger: Logger
    thread_pool: ThreadPool
    application_name: str
    poster: Optional[CarbonPoster] = None
    namespace_root: Optional[str] = NAMESPACE_ROOT
    metric_namespace: Optional[str] = METRIC_NAMESPACE
    pod_name: Optional[str] = None

    def __init__(self, options: GraphiteLoggerOptions):
        self.logger = get_logger(
            log_level=options.log_level,
            application_name=options.application_name,
            log_directory=options.log_directory
        )
        if "server_ip" in options.carbon_config and options.carbon_config["server_ip"] is not None:
            self.poster = CarbonPoster(**options.carbon_config)
        else:
            self.poster = None
        self.application_name = options.application_name
        self.thread_pool = ThreadPool(self.logger, options.thread_pool_size)
        self.namespace_root = options.namespace_root
        self.metric_namespace = options.metric_namespace
        self.pod_name = options.pod_name

    def get_metrics(self, name: str, mnemonic: str, hostname: str = None) -> Metrics:
        metrics: Metrics = Metrics(
            mnemonic=mnemonic,
            namespace=f"{self.namespace_root}.{self.metric_namespace}",
            name=name,
            hostname=hostname,
            meta={
                'pod': self.pod_name
            },
            counters={
                'exceptions': 0,
                'requests': 0,
                'responses': 0,
                'threads': threading.active_count(),
            },
            attributes={
                'request_time': 0,
                'request_time_ms': 0,
                'response_length': 0,
                'thread_pool_size': self.thread_pool.size,
            },
        )
        return metrics

    def log_metrics(self, metrics: Metrics) -> None:
        task_name_template = f"{metrics.mnemonic}_%s_{time.time_ns():x}_{random.getrandbits(8):02x}"
        if self.poster:
            self.thread_pool.start_task(
                task_name=task_name_template % "post_metrics",
                target=metrics.post_metrics,
                kwargs={"logger": self.logger, "poster": self.poster},
                blocking=False
            )
        self.thread_pool.start_task(
            task_name=task_name_template % "log_metrics",
            target=metrics.log_metrics,
            kwargs={"logger": self.logger},
            blocking=False
        )
