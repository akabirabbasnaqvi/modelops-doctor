from typing import Any


HEALTH_SCORE_WEIGHTS = {
    "performance": 0.35,
    "drift": 0.25,
    "data_quality": 0.20,
    "confidence": 0.10,
    "class_balance": 0.10,
}


def calculate_health_score(
    performance_score: float,
    drift_score: float,
    data_quality_score: float,
    confidence_score: float,
    class_balance_score: float,
) -> dict[str, Any]:
    """Calculate the weighted overall model-health score."""

    components = {
        "performance": _validate_score(
            performance_score,
            "performance_score",
        ),
        "drift": _validate_score(
            drift_score,
            "drift_score",
        ),
        "data_quality": _validate_score(
            data_quality_score,
            "data_quality_score",
        ),
        "confidence": _validate_score(
            confidence_score,
            "confidence_score",
        ),
        "class_balance": _validate_score(
            class_balance_score,
            "class_balance_score",
        ),
    }

    overall_score = sum(
        components[name] * HEALTH_SCORE_WEIGHTS[name] for name in HEALTH_SCORE_WEIGHTS
    )

    rounded_score = round(overall_score, 2)

    return {
        "health_score": rounded_score,
        "status": classify_health_status(rounded_score),
        "components": components,
        "weights": HEALTH_SCORE_WEIGHTS,
    }


def calculate_component_scores(
    metrics: dict[str, Any],
    drift: dict[str, Any],
    missing_rate: float,
) -> dict[str, float]:
    """Convert monitoring results into normalized 0-100 scores."""

    performance_value = metrics.get("f1")

    if performance_value is None:
        performance_value = metrics.get("accuracy")

    if performance_value is None:
        performance_score = 50.0
    else:
        performance_score = float(performance_value) * 100

    drift_rate = float(drift.get("drift_rate", 0.0))
    drift_score = max(0.0, 100.0 * (1.0 - drift_rate))

    normalized_missing_rate = min(
        max(float(missing_rate), 0.0),
        1.0,
    )
    data_quality_score = 100.0 * (1.0 - normalized_missing_rate)

    average_confidence = metrics.get("average_confidence")

    if average_confidence is None:
        confidence_score = 50.0
    else:
        confidence_score = float(average_confidence) * 100

    distribution = metrics.get("true_class_distribution") or metrics.get(
        "predicted_class_distribution", {}
    )

    class_balance_score = _calculate_class_balance_score(distribution)

    return {
        "performance_score": round(performance_score, 2),
        "drift_score": round(drift_score, 2),
        "data_quality_score": round(
            data_quality_score,
            2,
        ),
        "confidence_score": round(confidence_score, 2),
        "class_balance_score": round(
            class_balance_score,
            2,
        ),
    }


def classify_health_status(score: float) -> str:
    if score >= 90:
        return "excellent"

    if score >= 75:
        return "good"

    if score >= 60:
        return "warning"

    if score >= 40:
        return "risky"

    return "critical"


def _calculate_class_balance_score(
    distribution: dict[str, float],
) -> float:
    if not distribution:
        return 50.0

    proportions = [float(value) for value in distribution.values()]

    if len(proportions) == 1:
        return 0.0

    minimum = min(proportions)
    maximum = max(proportions)

    if maximum == 0:
        return 0.0

    return min(100.0, (minimum / maximum) * 100.0)


def _validate_score(
    score: float,
    score_name: str,
) -> float:
    numeric_score = float(score)

    if not 0 <= numeric_score <= 100:
        raise ValueError(f"{score_name} must be between 0 and 100.")

    return numeric_score
