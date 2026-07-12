from typing import Any


def generate_diagnosis(
    metrics: dict[str, Any],
    drift: dict[str, Any],
    health: dict[str, Any],
    missing_rate: float,
) -> dict[str, Any]:
    """Generate rule-based model-health findings."""

    findings: list[dict[str, str]] = []
    recommendations: list[str] = []

    f1_score = metrics.get("f1")

    if f1_score is not None and float(f1_score) < 0.70:
        findings.append(
            {
                "code": "LOW_F1",
                "severity": "high",
                "message": "The model F1-score is below 0.70.",
            }
        )
        recommendations.append(
            "Review misclassified examples and retrain the model "
            "with representative recent data."
        )

    drifted_features = drift.get("drifted_features", [])

    if drifted_features:
        findings.append(
            {
                "code": "FEATURE_DRIFT",
                "severity": "high",
                "message": (
                    "Feature drift was detected in: "
                    + ", ".join(drifted_features)
                    + "."
                ),
            }
        )
        recommendations.append(
            "Investigate upstream data changes and compare recent "
            "feature distributions with the training baseline."
        )

    average_confidence = metrics.get("average_confidence")

    if average_confidence is not None and float(average_confidence) < 0.70:
        findings.append(
            {
                "code": "LOW_CONFIDENCE",
                "severity": "medium",
                "message": ("Average model confidence is below 0.70."),
            }
        )
        recommendations.append(
            "Review low-confidence cases and evaluate probability "
            "calibration or decision-threshold adjustment."
        )

    low_confidence_rate = metrics.get("low_confidence_rate")

    if low_confidence_rate is not None and float(low_confidence_rate) > 0.20:
        findings.append(
            {
                "code": "HIGH_LOW_CONFIDENCE_RATE",
                "severity": "medium",
                "message": ("More than 20% of predictions have low confidence."),
            }
        )
        recommendations.append(
            "Inspect noisy inputs and difficult prediction segments."
        )

    if missing_rate > 0.05:
        findings.append(
            {
                "code": "MISSING_VALUES",
                "severity": "medium",
                "message": ("More than 5% of current feature values are missing."),
            }
        )
        recommendations.append(
            "Validate the upstream data pipeline and improve missing-value handling."
        )

    class_distribution = metrics.get("true_class_distribution") or metrics.get(
        "predicted_class_distribution", {}
    )

    if class_distribution:
        proportions = [float(value) for value in class_distribution.values()]

        if min(proportions) < 0.20:
            findings.append(
                {
                    "code": "CLASS_IMBALANCE",
                    "severity": "medium",
                    "message": (
                        "At least one class represents less than 20% "
                        "of monitored records."
                    ),
                }
            )
            recommendations.append(
                "Review minority-class recall and consider class "
                "weights, oversampling, or additional data collection."
            )

    if not findings:
        findings.append(
            {
                "code": "HEALTHY_MODEL",
                "severity": "low",
                "message": (
                    "No major performance, drift, confidence, or "
                    "data-quality problem was detected."
                ),
            }
        )
        recommendations.append(
            "Continue monitoring the model with new prediction batches."
        )

    risk_level = _determine_risk_level(
        health_score=float(health["health_score"]),
        findings=findings,
    )

    retraining_recommended = risk_level in {"high", "critical"} or any(
        finding["code"] in {"LOW_F1", "FEATURE_DRIFT"} for finding in findings
    )

    return {
        "summary": _build_summary(
            health_score=float(health["health_score"]),
            status=str(health["status"]),
            finding_count=len(findings),
        ),
        "risk_level": risk_level,
        "retraining_recommended": retraining_recommended,
        "findings": findings,
        "recommendations": list(dict.fromkeys(recommendations)),
    }


def _determine_risk_level(
    health_score: float,
    findings: list[dict[str, str]],
) -> str:
    if health_score < 40:
        return "critical"

    if health_score < 60:
        return "high"

    if any(finding["severity"] == "high" for finding in findings):
        return "high"

    if health_score < 75:
        return "medium"

    return "low"


def _build_summary(
    health_score: float,
    status: str,
    finding_count: int,
) -> str:
    return (
        f"Model health score is {health_score:.2f}/100 "
        f"with status '{status}'. "
        f"The diagnosis engine produced {finding_count} finding(s)."
    )
