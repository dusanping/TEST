from __future__ import annotations

import time
from typing import Any

from host_load_analyzer.clients.monitor_client import MonitorClient


class MetricCollector:
    """Component-oriented collector, easy to extend for new component metrics."""

    def __init__(self, monitor_client: MonitorClient) -> None:
        self.monitor = monitor_client
        self.cache: dict[str, dict[str, Any]] = {}

    def collect_component_metrics(
        self,
        component: str,
        config: dict,
        start_time: int | None = None,
        end_time: int | None = None,
        use_cache: bool = False,
    ) -> dict[str, list[dict[str, Any]]]:
        data_source = config.get("data_source", "v2_metrics")
        metrics_config = config.get("metrics", {})
        step = config.get("step", "30s")
        tsdbid = config.get("tsdbid")

        if end_time is None:
            end_time = int(time.time())
        if start_time is None:
            start_time = end_time - 3600

        cache_key = f"{component}:{start_time}:{end_time}:{step}:{tsdbid}"
        if use_cache and cache_key in self.cache and time.time() - self.cache[cache_key]["timestamp"] < 300:
            return self.cache[cache_key]["data"]

        metrics = self.monitor.batch_query_range(
            data_source=data_source,
            queries=metrics_config,
            start_time=start_time,
            end_time=end_time,
            step=step,
            tsdbid=tsdbid,
        )

        self.cache[cache_key] = {"data": metrics, "timestamp": time.time()}
        return metrics
