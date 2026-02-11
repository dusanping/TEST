from __future__ import annotations

from statistics import mean, median


def to_points(values: list[list[str | float]]) -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for raw_ts, raw_val in values:
        try:
            points.append((int(float(raw_ts)), float(raw_val)))
        except (ValueError, TypeError):
            continue
    return points


def summarize(points: list[tuple[int, float]]) -> dict[str, float]:
    if not points:
        return {"avg": 0.0, "p50": 0.0, "max": 0.0, "min": 0.0}
    vals = [v for _, v in points]
    return {
        "avg": float(mean(vals)),
        "p50": float(median(vals)),
        "max": float(max(vals)),
        "min": float(min(vals)),
    }


def percentile(points: list[tuple[int, float]], pct: float) -> float:
    if not points:
        return 0.0
    vals = sorted(v for _, v in points)
    index = int((len(vals) - 1) * pct)
    return float(vals[index])


def linear_slope_per_hour(points: list[tuple[int, float]]) -> float:
    """Least squares slope in unit/hour."""
    if len(points) < 2:
        return 0.0

    xs = [float(ts - points[0][0]) / 3600.0 for ts, _ in points]
    ys = [v for _, v in points]
    n = len(xs)
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys, strict=True))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0
    return numerator / denominator
