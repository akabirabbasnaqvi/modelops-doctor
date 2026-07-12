import pandas as pd

from app.mlops.drift import (
    analyze_feature_drift,
    calculate_categorical_drift,
    calculate_ks_test,
    calculate_numeric_psi,
)


def test_numeric_psi_is_small_for_similar_data() -> None:
    psi = calculate_numeric_psi(
        reference_values=list(range(1, 101)),
        current_values=list(range(1, 101)),
    )

    assert psi < 0.01


def test_numeric_psi_detects_shift() -> None:
    psi = calculate_numeric_psi(
        reference_values=list(range(1, 101)),
        current_values=list(range(101, 201)),
    )

    assert psi > 0.25


def test_ks_test_detects_distribution_change() -> None:
    result = calculate_ks_test(
        reference_values=list(range(1, 101)),
        current_values=list(range(101, 201)),
    )

    assert result["statistic"] > 0.9
    assert result["p_value"] < 0.05


def test_categorical_drift() -> None:
    result = calculate_categorical_drift(
        reference_values=["A"] * 80 + ["B"] * 20,
        current_values=["A"] * 30 + ["B"] * 70,
    )

    assert result["total_variation_distance"] == 0.5


def test_feature_drift_analysis() -> None:
    reference = pd.DataFrame(
        {
            "age": list(range(20, 40)),
            "contract": ["monthly"] * 10 + ["yearly"] * 10,
        }
    )

    current = pd.DataFrame(
        {
            "age": list(range(60, 80)),
            "contract": ["monthly"] * 2 + ["yearly"] * 18,
        }
    )

    result = analyze_feature_drift(reference, current)

    assert result["feature_count"] == 2
    assert result["drifted_feature_count"] >= 1
    assert "age" in result["drifted_features"]
