from app.mlops.diagnosis import generate_diagnosis


def test_diagnosis_detects_drift_and_low_performance() -> None:
    diagnosis = generate_diagnosis(
        metrics={
            "f1": 0.60,
            "average_confidence": 0.65,
            "low_confidence_rate": 0.30,
            "true_class_distribution": {
                "0": 0.85,
                "1": 0.15,
            },
        },
        drift={
            "drifted_features": [
                "age",
                "monthly_charges",
            ]
        },
        health={
            "health_score": 55.0,
            "status": "risky",
        },
        missing_rate=0.10,
    )

    finding_codes = {finding["code"] for finding in diagnosis["findings"]}

    assert "LOW_F1" in finding_codes
    assert "FEATURE_DRIFT" in finding_codes
    assert "LOW_CONFIDENCE" in finding_codes
    assert "MISSING_VALUES" in finding_codes
    assert "CLASS_IMBALANCE" in finding_codes
    assert diagnosis["risk_level"] == "high"
    assert diagnosis["retraining_recommended"] is True


def test_healthy_diagnosis() -> None:
    diagnosis = generate_diagnosis(
        metrics={
            "f1": 0.90,
            "average_confidence": 0.88,
            "low_confidence_rate": 0.05,
            "true_class_distribution": {
                "0": 0.50,
                "1": 0.50,
            },
        },
        drift={"drifted_features": []},
        health={
            "health_score": 91.0,
            "status": "excellent",
        },
        missing_rate=0.0,
    )

    assert diagnosis["risk_level"] == "low"
    assert diagnosis["retraining_recommended"] is False
    assert diagnosis["findings"][0]["code"] == "HEALTHY_MODEL"
