from __future__ import annotations

from host_load_analyzer.core.models import CapacityForecast
from host_load_analyzer.utils.series import linear_slope_per_hour


def forecast_to_threshold(
    points: list[tuple[int, float]],
    threshold: float,
) -> CapacityForecast:
    slope = linear_slope_per_hour(points)
    current_value = points[-1][1] if points else 0.0

    if slope <= 0:
        eta = None
    else:
        distance = threshold - current_value
        eta = 0.0 if distance <= 0 else distance / slope

    return CapacityForecast(
        slope_per_hour=slope,
        current_value=current_value,
        threshold=threshold,
        eta_hours=eta,
    )
