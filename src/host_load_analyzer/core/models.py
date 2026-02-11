from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TimePoint:
    ts: int
    value: float


@dataclass
class Anomaly:
    ts: int
    value: float
    reason: str
    severity: str = "medium"


@dataclass
class CapacityForecast:
    slope_per_hour: float
    current_value: float
    threshold: float
    eta_hours: float | None


@dataclass
class MetricReport:
    name: str
    summary: dict[str, float]
    anomalies: list[Anomaly] = field(default_factory=list)
    forecast: CapacityForecast | None = None


@dataclass
class HostAnalysisReport:
    host: str
    window_start: int
    window_end: int
    cpu: MetricReport
    disk: MetricReport
