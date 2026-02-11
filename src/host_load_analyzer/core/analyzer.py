from __future__ import annotations

from host_load_analyzer.components.collector import MetricCollector
from host_load_analyzer.components.promql import cpu_busy_query, disk_used_percent_query
from host_load_analyzer.core.anomaly import robust_anomaly_check
from host_load_analyzer.core.forecast import forecast_to_threshold
from host_load_analyzer.core.models import HostAnalysisReport, MetricReport
from host_load_analyzer.utils.series import summarize, to_points


class HostLoadAnalyzer:
    def __init__(self, collector: MetricCollector) -> None:
        self.collector = collector

    def analyze_host(
        self,
        host_ident: str,
        primary_ip: str | None,
        mountpoint: str,
        start_time: int,
        end_time: int,
        data_source: str = "v2_metrics",
        tsdbid: int | None = None,
    ) -> HostAnalysisReport:
        query_map = {
            "cpu": cpu_busy_query(host_ident, primary_ip),
            "disk": disk_used_percent_query(host_ident, mountpoint),
        }
        config = {
            "data_source": data_source,
            "step": "30s",
            "tsdbid": tsdbid,
            "metrics": query_map,
        }
        metrics = self.collector.collect_component_metrics(
            component="host",
            config=config,
            start_time=start_time,
            end_time=end_time,
            use_cache=False,
        )

        cpu_points = self._flatten_points(metrics.get("cpu", []))
        disk_points = self._flatten_points(metrics.get("disk", []))

        cpu_report = MetricReport(
            name="cpu_busy_percent",
            summary=summarize(cpu_points),
            anomalies=robust_anomaly_check(cpu_points, high_threshold=85.0, low_threshold=0.1, z_threshold=5.0),
            forecast=forecast_to_threshold(cpu_points, threshold=90.0),
        )
        disk_report = MetricReport(
            name="disk_used_percent",
            summary=summarize(disk_points),
            anomalies=robust_anomaly_check(disk_points, high_threshold=90.0, low_threshold=5.0, z_threshold=4.0),
            forecast=forecast_to_threshold(disk_points, threshold=85.0),
        )

        return HostAnalysisReport(
            host=host_ident,
            window_start=start_time,
            window_end=end_time,
            cpu=cpu_report,
            disk=disk_report,
        )

    @staticmethod
    def _flatten_points(series_result: list[dict]) -> list[tuple[int, float]]:
        points: list[tuple[int, float]] = []
        for series in series_result:
            values = series.get("values", [])
            points.extend(to_points(values))
        points.sort(key=lambda x: x[0])
        return points
