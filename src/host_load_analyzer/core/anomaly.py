from __future__ import annotations

from statistics import median

from host_load_analyzer.core.models import Anomaly


def robust_anomaly_check(
    points: list[tuple[int, float]],
    high_threshold: float,
    low_threshold: float | None = None,
    z_threshold: float = 4.0,
) -> list[Anomaly]:
    if len(points) < 8:
        return []

    vals = [v for _, v in points]
    med = median(vals)
    mad = median([abs(v - med) for v in vals]) or 1e-6

    anomalies: list[Anomaly] = []
    for ts, value in points:
        robust_z = 0.6745 * (value - med) / mad
        if value >= high_threshold:
            anomalies.append(Anomaly(ts=ts, value=value, reason=f"value >= {high_threshold}", severity="high"))
            continue
        if low_threshold is not None and value <= low_threshold:
            anomalies.append(Anomaly(ts=ts, value=value, reason=f"value <= {low_threshold}", severity="medium"))
            continue
        if abs(robust_z) >= z_threshold:
            anomalies.append(
                Anomaly(
                    ts=ts,
                    value=value,
                    reason=f"robust_z={robust_z:.2f} exceeds {z_threshold}",
                    severity="medium",
                )
            )
    return anomalies
