from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


EPSILON = 1e-6


def calculate_numeric_psi(
    reference_values: list,
    current_values: list,
    bins: int = 10,
) -> float:
    """Calculate Population Stability Index for numeric values."""

    reference = _clean_numeric_values(reference_values)
    current = _clean_numeric_values(current_values)

    if reference.size == 0 or current.size == 0:
        raise ValueError("Reference and current values must contain numeric data.")

    if np.all(reference == reference[0]):
        boundaries = np.array(
            [
                reference[0] - 0.5,
                reference[0] + 0.5,
            ]
        )
    else:
        quantiles = np.linspace(0, 1, bins + 1)
        boundaries = np.unique(np.quantile(reference, quantiles))

        boundaries[0] = -np.inf
        boundaries[-1] = np.inf

    reference_counts, _ = np.histogram(reference, bins=boundaries)
    current_counts, _ = np.histogram(current, bins=boundaries)

    reference_proportions = reference_counts / reference_counts.sum()
    current_proportions = current_counts / current_counts.sum()

    reference_proportions = np.clip(
        reference_proportions,
        EPSILON,
        None,
    )
    current_proportions = np.clip(
        current_proportions,
        EPSILON,
        None,
    )

    psi_values = (current_proportions - reference_proportions) * np.log(
        current_proportions / reference_proportions
    )

    return float(np.sum(psi_values))


def calculate_ks_test(
    reference_values: list,
    current_values: list,
) -> dict[str, float]:
    """Run the two-sample Kolmogorov-Smirnov test."""

    reference = _clean_numeric_values(reference_values)
    current = _clean_numeric_values(current_values)

    if reference.size == 0 or current.size == 0:
        raise ValueError("Reference and current values must contain numeric data.")

    result = ks_2samp(reference, current)

    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def calculate_categorical_drift(
    reference_values: list,
    current_values: list,
) -> dict[str, Any]:
    """Compare categorical proportions using total variation distance."""

    reference = _clean_categorical_values(reference_values)
    current = _clean_categorical_values(current_values)

    if not reference or not current:
        raise ValueError("Reference and current categories cannot be empty.")

    categories = sorted(set(reference) | set(current))

    reference_distribution = _category_distribution(
        reference,
        categories,
    )
    current_distribution = _category_distribution(
        current,
        categories,
    )

    absolute_differences = {
        category: abs(current_distribution[category] - reference_distribution[category])
        for category in categories
    }

    total_variation_distance = 0.5 * sum(absolute_differences.values())

    return {
        "reference_distribution": reference_distribution,
        "current_distribution": current_distribution,
        "absolute_differences": absolute_differences,
        "total_variation_distance": float(total_variation_distance),
    }


def analyze_feature_drift(
    reference_dataframe: pd.DataFrame,
    current_dataframe: pd.DataFrame,
    psi_warning_threshold: float = 0.10,
    psi_critical_threshold: float = 0.25,
    ks_p_value_threshold: float = 0.05,
    categorical_threshold: float = 0.10,
) -> dict[str, Any]:
    """Analyze drift for shared numeric and categorical features."""

    shared_columns = sorted(
        set(reference_dataframe.columns) & set(current_dataframe.columns)
    )

    feature_results: dict[str, Any] = {}
    drifted_features: list[str] = []

    for column in shared_columns:
        reference_series = reference_dataframe[column]
        current_series = current_dataframe[column]

        is_numeric = pd.api.types.is_numeric_dtype(
            reference_series
        ) and pd.api.types.is_numeric_dtype(current_series)

        if is_numeric:
            psi = calculate_numeric_psi(
                reference_series.tolist(),
                current_series.tolist(),
            )

            ks_result = calculate_ks_test(
                reference_series.tolist(),
                current_series.tolist(),
            )

            if psi >= psi_critical_threshold:
                severity = "critical"
            elif (
                psi >= psi_warning_threshold
                or ks_result["p_value"] < ks_p_value_threshold
            ):
                severity = "warning"
            else:
                severity = "stable"

            feature_results[column] = {
                "feature_type": "numeric",
                "psi": psi,
                "ks_statistic": ks_result["statistic"],
                "ks_p_value": ks_result["p_value"],
                "severity": severity,
            }
        else:
            categorical_result = calculate_categorical_drift(
                reference_series.tolist(),
                current_series.tolist(),
            )

            distance = categorical_result["total_variation_distance"]

            if distance >= 0.25:
                severity = "critical"
            elif distance >= categorical_threshold:
                severity = "warning"
            else:
                severity = "stable"

            feature_results[column] = {
                "feature_type": "categorical",
                **categorical_result,
                "severity": severity,
            }

        if feature_results[column]["severity"] != "stable":
            drifted_features.append(column)

    feature_count = len(feature_results)

    drift_rate = len(drifted_features) / feature_count if feature_count else 0.0

    return {
        "feature_count": feature_count,
        "drifted_feature_count": len(drifted_features),
        "drift_rate": float(drift_rate),
        "drifted_features": drifted_features,
        "features": feature_results,
    }


def _clean_numeric_values(values: list) -> np.ndarray:
    numeric = pd.to_numeric(
        pd.Series(values),
        errors="coerce",
    ).dropna()

    return numeric.to_numpy(dtype=float)


def _clean_categorical_values(values):
    return ["MISSING" if pd.isna(value) else str(value) for value in values]


def _category_distribution(
    values: list[str],
    categories: list[str],
) -> dict[str, float]:
    total = len(values)

    return {category: values.count(category) / total for category in categories}
