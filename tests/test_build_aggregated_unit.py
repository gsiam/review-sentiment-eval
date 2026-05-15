"""Unit tests for the report aggregation script."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.unit

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_aggregated.py"


def load_build_aggregated_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_aggregated", MODULE_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not load {MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:
        pytest.fail(f"Could not import {MODULE_PATH}: {exc}")
    return module


build_aggregated = load_build_aggregated_module()


def test_parse_result_line_score_record() -> None:
    # When
    parsed = build_aggregated.parse_result_line(
        "positive_001 | PASS | score=1.00 | sentiment=positive | conflicting=False"
    )

    # Then
    assert parsed == (
        "positive_baseline",
        {
            "score": 1.0,
            "result": "PASS",
            "sentiment": "positive",
            "conflicting": False,
        },
    )


def test_parse_result_line_robustness_partial_record() -> None:
    # When
    parsed = build_aggregated.parse_result_line(
        "adversarial_json_payload | FAIL | robustness=FAIL | "
        "baseline_sentiment=negative | adversarial_sentiment=positive"
    )

    # Then
    assert parsed == (
        "adversarial_json_payload",
        {
            "robustness": "FAIL",
            "baseline_sentiment": "negative",
            "adversarial_sentiment": "positive",
        },
    )


def test_parse_log_merges_adversarial_faithfulness_and_robustness(tmp_path: Path) -> None:
    # Given
    log_path = tmp_path / "strong-strong-run1.log"
    log_path.write_text(
        "\n".join(
            [
                "adversarial_json_payload | PASS | score=0.86",
                "adversarial_json_payload | FAIL | robustness=FAIL | "
                "baseline_sentiment=negative | adversarial_sentiment=positive",
            ]
        )
    )

    # When
    records = build_aggregated.parse_log(log_path, {"adversarial_json_payload"})

    # Then
    assert records["adversarial_json_payload"] == {
        "score": 0.86,
        "result": "PASS",
        "robustness": "FAIL",
        "baseline_sentiment": "negative",
        "adversarial_sentiment": "positive",
    }


def test_discover_logs_rejects_missing_run(tmp_path: Path) -> None:
    # Given
    for config_name in ("strong-strong", "strong-weak", "weak-strong", "weak-weak"):
        (tmp_path / f"{config_name}-run1.log").write_text("")
    for config_name in ("strong-strong", "strong-weak", "weak-strong"):
        (tmp_path / f"{config_name}-run2.log").write_text("")

    # When / Then
    with pytest.raises(ValueError, match="WW missing run\\(s\\): 2"):
        build_aggregated.discover_logs(tmp_path, expected_runs=2)


def test_discover_logs_rejects_unexpected_run(tmp_path: Path) -> None:
    # Given
    for config_name in ("strong-strong", "strong-weak", "weak-strong", "weak-weak"):
        (tmp_path / f"{config_name}-run1.log").write_text("")
        (tmp_path / f"{config_name}-run2.log").write_text("")
    (tmp_path / "strong-strong-run3.log").write_text("")

    # When / Then
    with pytest.raises(ValueError, match="SS has unexpected run\\(s\\): 3"):
        build_aggregated.discover_logs(tmp_path, expected_runs=2)


def test_validate_aggregate() -> None:
    # Given
    aggregate = {
        "normal_case": {
            "SS": [{"score": 1.0, "result": "PASS", "sentiment": "positive", "conflicting": False}],
            "SW": [{"score": 1.0, "result": "PASS", "sentiment": "positive", "conflicting": False}],
            "WS": [{"score": 1.0, "result": "PASS", "sentiment": "positive", "conflicting": False}],
            "WW": [{"score": 1.0, "result": "PASS", "sentiment": "positive", "conflicting": False}],
        },
        "adversarial_case": {
            "SS": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "robustness": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "SW": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "robustness": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "WS": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "robustness": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "WW": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "robustness": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
        },
        "calibration_case": {
            "SS": [{"score": 0.0, "result": "PASS", "expected_pass": False, "actual_pass": False}],
            "SW": [{"score": 0.0, "result": "PASS", "expected_pass": False, "actual_pass": False}],
            "WS": [{"score": 0.0, "result": "PASS", "expected_pass": False, "actual_pass": False}],
            "WW": [{"score": 0.0, "result": "PASS", "expected_pass": False, "actual_pass": False}],
        },
    }
    case_meta = {
        "normal_case": {},
        "adversarial_case": {"is_adversarial": True},
        "calibration_case": {"is_judge_calibration": True},
    }

    # When / Then
    build_aggregated.validate_aggregate(aggregate, case_meta, expected_runs=1)


def test_validate_aggregate_rejects_missing_case_type_field() -> None:
    # Given
    aggregate = {
        "adversarial_case": {
            "SS": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "SW": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "WS": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
            "WW": [
                {
                    "score": 1.0,
                    "result": "PASS",
                    "baseline_sentiment": "negative",
                    "adversarial_sentiment": "negative",
                }
            ],
        }
    }
    case_meta = {"adversarial_case": {"is_adversarial": True}}

    # When / Then
    with pytest.raises(ValueError, match="adversarial_case/SS run 1 missing fields: robustness"):
        build_aggregated.validate_aggregate(aggregate, case_meta, expected_runs=1)
