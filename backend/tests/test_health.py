from app.mlops.health import (
    calculate_component_scores,
    calculate_health_score,
    classify_health_status,
)


def test_weighted_health_score() -> None:
    result = calculate_health_score(
        performance_score=90,
        drift_score=80,
        data_quality_score=100,
        confidence_score=85,
        class_balance_score=100,
    )

    assert result["health_score"] == 90.0
    assert result["status"] == "excellent"


def test_health_status_boundaries() -> None:
    assert classify_health_status(95) == "excellent"
    assert classify_health_status(80) == "good"
    assert classify_health_status(65) == "warning"
    assert classify_health_status(50) == "risky"
    assert classify_health_status(30) == "critical"


def test_component_score_conversion() -> None:
    result = calculate_component_scores(
        metrics={
            "f1": 0.80,
            "average_confidence": 0.90,
            "true_class_distribution": {
                "0": 0.50,
                "1": 0.50,
            },
        },
        drift={"drift_rate": 0.20},
        missing_rate=0.05,
    )

    assert result["performance_score"] == 80.0
    assert result["drift_score"] == 80.0
    assert result["data_quality_score"] == 95.0
    assert result["confidence_score"] == 90.0
    assert result["class_balance_score"] == 100.0
