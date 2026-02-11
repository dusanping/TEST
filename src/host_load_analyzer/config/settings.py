"""Runtime configuration.

You can override defaults via environment variables or by importing and editing
`MONITOR_CONFIG` and `MONITOR_TSDB_ID` in your own entrypoint.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DataSourceConfig:
    base_url: str
    username: str
    password: str

    @property
    def credentials(self) -> dict[str, str]:
        return {
            "username": self.username,
            "password": self.password,
        }


MONITOR_CONFIG: dict[str, dict] = {
    "v2_metrics": {
        "base_url": os.getenv("MONITOR_BASE_URL", "https://monitor.example.com"),
        "credentials": {
            "username": os.getenv("MONITOR_USERNAME", "system"),
            "password": os.getenv("MONITOR_PASSWORD", "changeme"),
        },
    }
}

# Extend as needed for custom component -> tsdb id mapping.
MONITOR_TSDB_ID: dict[str, int] = {
    "es_metrics_id": int(os.getenv("ES_METRICS_ID", "0")),
}
