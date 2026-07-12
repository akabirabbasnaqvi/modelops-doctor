import pytest

from app.mlops.metrics import calculate_classification_metrics


def test_classification_metrics() -> None:
    result = calculate_classification_metrics(
        true_labels=[1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        predicted_labels=[1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
        confidences=[
            0.91,
            0.88,
            0.82,
            0.95,
            0.79,
            0.87,
            0.56,
            0.93,
            0.84,
            0.89,
        ],
        positive_class=1,
    )

    assert result["sample_count"] == 10
    assert result["accuracy"] == pytest.approx(0.9)
    assert result["precision"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(0.8)
    assert result["f1"] == pytest.approx(0.888888, rel=1e-5)
    assert result["confusion_matrix"] == [[5, 0], [1, 4]]
    assert result["average_confidence"] == pytest.approx(0.844)
    assert result["low_confidence_rate"] == pytest.approx(0.1)
