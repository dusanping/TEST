from host_load_analyzer.core.anomaly import robust_anomaly_check
from host_load_analyzer.core.forecast import forecast_to_threshold


def test_robust_anomaly_high_threshold():
    points = [(i, 20.0) for i in range(1, 20)] + [(21, 95.0)]
    result = robust_anomaly_check(points, high_threshold=85.0)
    assert any(a.value == 95.0 for a in result)


def test_forecast_eta_positive_slope():
    points = [(0, 50.0), (3600, 55.0), (7200, 60.0)]
    forecast = forecast_to_threshold(points, threshold=70.0)
    assert forecast.slope_per_hour > 0
    assert forecast.eta_hours is not None
    assert 1.5 < forecast.eta_hours < 2.5
