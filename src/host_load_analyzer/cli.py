from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict

from host_load_analyzer.clients.monitor_client import MonitorClient
from host_load_analyzer.components.collector import MetricCollector
from host_load_analyzer.config.settings import MONITOR_CONFIG
from host_load_analyzer.core.analyzer import HostLoadAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Host CPU/Disk load analyzer")
    parser.add_argument("--host", required=True, help="Host ident/instance")
    parser.add_argument("--primary-ip", default=None, help="Optional __primary_ip__ label")
    parser.add_argument("--mountpoint", default="/", help="Disk mountpoint")
    parser.add_argument("--hours", type=int, default=24, help="Time window size in hours")
    parser.add_argument("--data-source", default="v2_metrics")
    parser.add_argument("--tsdbid", type=int, default=None)
    return parser


def format_eta(hours: float | None) -> str:
    if hours is None:
        return "不会达到阈值（趋势非增长）"
    if hours <= 0:
        return "已达到阈值"
    return f"约 {hours:.2f} 小时"


def main() -> None:
    args = build_parser().parse_args()
    end_time = int(time.time())
    start_time = end_time - args.hours * 3600

    monitor = MonitorClient(monitor_config=MONITOR_CONFIG)
    collector = MetricCollector(monitor)
    analyzer = HostLoadAnalyzer(collector)

    report = analyzer.analyze_host(
        host_ident=args.host,
        primary_ip=args.primary_ip,
        mountpoint=args.mountpoint,
        start_time=start_time,
        end_time=end_time,
        data_source=args.data_source,
        tsdbid=args.tsdbid,
    )

    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    print("\n=== 人类可读结论 ===")
    print(f"CPU均值 {report.cpu.summary['avg']:.2f}% | 最大 {report.cpu.summary['max']:.2f}%")
    print(f"CPU异常点数量: {len(report.cpu.anomalies)}")
    print(f"CPU达到90%预计: {format_eta(report.cpu.forecast.eta_hours if report.cpu.forecast else None)}")

    print(f"磁盘均值 {report.disk.summary['avg']:.2f}% | 最大 {report.disk.summary['max']:.2f}%")
    print(f"磁盘异常点数量: {len(report.disk.anomalies)}")
    print(f"磁盘达到85%预计: {format_eta(report.disk.forecast.eta_hours if report.disk.forecast else None)}")


if __name__ == "__main__":
    main()
