from __future__ import annotations

import time
from typing import Any

import requests


class MonitorClient:
    """Prometheus gateway client with token cache."""

    def __init__(self, monitor_config: dict[str, dict], logger: Any | None = None) -> None:
        self.tokens: dict[str, dict[str, Any]] = {}
        self.monitor_config = monitor_config
        self.logger = logger

    def _get_auth_token(self, data_source: str) -> str:
        """Get auth token and cache for 1 hour."""
        current = self.tokens.get(data_source)
        if current and time.time() - current["timestamp"] < 3600:
            return str(current["token"])

        config = self.monitor_config.get(data_source)
        if not config:
            raise ValueError(f"Unknown data source: {data_source}")

        auth_url = f"{config['base_url']}/oauth/systemLogin"
        headers = {"Content-Type": "application/json", "accept": "*/*"}

        response = requests.post(auth_url, headers=headers, json=config["credentials"], timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()
        token = data.get("data")
        if not token:
            raise RuntimeError(f"Token missing in response: {data}")

        self.tokens[data_source] = {"token": token, "timestamp": time.time()}
        return str(token)

    def query_promql_range(
        self,
        data_source: str,
        promql: str,
        start_time: int,
        end_time: int,
        step: str = "30s",
        tsdbid: int | None = None,
    ) -> list[dict[str, Any]]:
        """Range query against Prometheus compatible API."""
        token = self._get_auth_token(data_source)
        config = self.monitor_config[data_source]

        if tsdbid:
            base_url = f"{config['base_url']}/prom/redirect/{tsdbid}/api/v1/query_range"
        else:
            base_url = f"{config['base_url']}/prom/redirect/api/v1/query_range"

        headers = {
            "Accept": "application/json, text/plain, */*",
            "x-token": token,
        }
        params = {
            "query": promql,
            "start": start_time,
            "end": end_time,
            "step": step,
        }

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=30, verify=False)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success":
                return list(data.get("data", {}).get("result", []))
            return []
        except Exception as exc:  # noqa: BLE001
            if self.logger:
                self.logger.error("Range query failed: %s | promql=%s", exc, promql)
            return []

    def batch_query_range(
        self,
        data_source: str,
        queries: dict[str, str],
        start_time: int,
        end_time: int,
        step: str = "30s",
        tsdbid: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        results: dict[str, list[dict[str, Any]]] = {}
        for metric_name, promql in queries.items():
            results[metric_name] = self.query_promql_range(
                data_source=data_source,
                promql=promql,
                start_time=start_time,
                end_time=end_time,
                step=step,
                tsdbid=tsdbid,
            )
            time.sleep(0.1)
        return results
