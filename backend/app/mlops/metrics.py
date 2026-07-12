from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)


def calculate_classification_metrics(
    true_labels: list,
    predicted_labels: list,
    confidences: list | None = None,
    positive_class: str | int | None = None,
    low_confidence_threshold: float = 0.60,
) -> dict[str, Any]:
    """Calculate classification performance and confidence metrics."""

    if not true_labels:
        raise ValueError("True labels cannot be empty.")

    if len(true_labels) != len(predicted_labels):
        raise ValueError("True labels and predicted labels must have equal lengths.")

    normalized_true = [str(label) for label in true_labels]
    normalized_predicted = [str(label) for label in predicted_labels]

    labels = sorted(set(normalized_true) | set(normalized_predicted))

    if positive_class is not None:
        positive_label = str(positive_class)
    elif len(labels) == 2:
        positive_label = labels[-1]
    else:
        positive_label = None

    average_method = "binary" if len(labels) == 2 else "weighted"

    metric_arguments: dict[str, Any] = {
        "average": average_method,
        "zero_division": 0,
    }

    if average_method == "binary":
        metric_arguments["pos_label"] = positive_label

    accuracy = accuracy_score(
        normalized_true,
        normalized_predicted,
    )

    precision = precision_score(
        normalized_true,
        normalized_predicted,
        **metric_arguments,
    )

    recall = recall_score(
        normalized_true,
        normalized_predicted,
        **metric_arguments,
    )

    f1 = f1_score(
        normalized_true,
        normalized_predicted,
        **metric_arguments,
    )

    matrix = confusion_matrix(
        normalized_true,
        normalized_predicted,
        labels=labels,
    )

    per_class_precision, per_class_recall, per_class_f1, support = (
        precision_recall_fscore_support(
            normalized_true,
            normalized_predicted,
            labels=labels,
            zero_division=0,
        )
    )

    per_class = {
        label: {
            "precision": float(per_class_precision[index]),
            "recall": float(per_class_recall[index]),
            "f1": float(per_class_f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }

    true_distribution = _calculate_distribution(normalized_true)
    predicted_distribution = _calculate_distribution(normalized_predicted)

    result: dict[str, Any] = {
        "sample_count": len(normalized_true),
        "labels": labels,
        "positive_class": positive_label,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "error_rate": float(1.0 - accuracy),
        "confusion_matrix": matrix.tolist(),
        "per_class": per_class,
        "true_class_distribution": true_distribution,
        "predicted_class_distribution": predicted_distribution,
        "roc_auc": None,
        "average_confidence": None,
        "low_confidence_rate": None,
        "minimum_confidence": None,
        "maximum_confidence": None,
    }

    if confidences is not None:
        confidence_values = np.asarray(confidences, dtype=float)

        if len(confidence_values) != len(normalized_true):
            raise ValueError("Confidence values and labels must have equal lengths.")

        if np.any(confidence_values < 0) or np.any(confidence_values > 1):
            raise ValueError("Confidence values must be between 0 and 1.")

        result["average_confidence"] = float(np.mean(confidence_values))
        result["low_confidence_rate"] = float(
            np.mean(confidence_values < low_confidence_threshold)
        )
        result["minimum_confidence"] = float(np.min(confidence_values))
        result["maximum_confidence"] = float(np.max(confidence_values))

        if len(labels) == 2 and positive_label is not None:
            binary_true = [
                1 if label == positive_label else 0 for label in normalized_true
            ]

            try:
                result["roc_auc"] = float(roc_auc_score(binary_true, confidence_values))
            except ValueError:
                result["roc_auc"] = None

    return result


def calculate_unlabeled_prediction_metrics(
    predicted_labels: list,
    confidences: list | None = None,
    low_confidence_threshold: float = 0.60,
) -> dict[str, Any]:
    """Calculate monitoring statistics when true labels are unavailable."""

    if not predicted_labels:
        raise ValueError("Predicted labels cannot be empty.")

    normalized_predictions = [str(label) for label in predicted_labels]

    result: dict[str, Any] = {
        "sample_count": len(normalized_predictions),
        "predicted_class_distribution": _calculate_distribution(normalized_predictions),
        "average_confidence": None,
        "low_confidence_rate": None,
        "minimum_confidence": None,
        "maximum_confidence": None,
    }

    if confidences is not None:
        confidence_values = np.asarray(confidences, dtype=float)

        if len(confidence_values) != len(normalized_predictions):
            raise ValueError(
                "Confidence values and predictions must have equal lengths."
            )

        if np.any(confidence_values < 0) or np.any(confidence_values > 1):
            raise ValueError("Confidence values must be between 0 and 1.")

        result["average_confidence"] = float(np.mean(confidence_values))
        result["low_confidence_rate"] = float(
            np.mean(confidence_values < low_confidence_threshold)
        )
        result["minimum_confidence"] = float(np.min(confidence_values))
        result["maximum_confidence"] = float(np.max(confidence_values))

    return result


def _calculate_distribution(values: list[str]) -> dict[str, float]:
    total = len(values)

    return {label: values.count(label) / total for label in sorted(set(values))}
