"""Test harness for summarization evaluation (integration tests - real API)."""

import logging
from typing import Any

import pytest

from llm_eval.summarizer import Summarizer
from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator
from llm_eval.robustness_checker import RobustnessChecker

pytestmark = pytest.mark.integration

_result_logger = logging.getLogger("llm_eval.results")


_MAX_INPUT_PREVIEW = 100


def _log_input(case_id: str, text: str, *, injection: str = "") -> None:
    preview = text if len(text) <= _MAX_INPUT_PREVIEW else text[:_MAX_INPUT_PREVIEW] + "..."
    msg = "%-30s | input: %s"
    args: list[str] = [case_id, preview]
    if injection:
        msg += " | injection: %s"
        args.append(injection)
    _result_logger.info(msg, *args)


def _log_result(case_id: str, status: str, parts: list[str]) -> None:
    _result_logger.info("%-30s | %s | %s", case_id, status, " | ".join(parts))


class TestSummarizationFaithfulness:
    @pytest.mark.ragas_ci
    def test_evaluate(
        self,
        normal_case: dict[str, Any],
        summarizer: Summarizer,
        faithfulness_evaluator: FaithfulnessEvaluator,
    ):
        # When
        _log_input(normal_case["id"], normal_case["source_text"])
        result = summarizer.summarize(normal_case["source_text"])
        faithfulness = faithfulness_evaluator.evaluate(
            source_text=normal_case["source_text"],
            summary=result.summary,
        )

        # Then
        _log_result(
            normal_case["id"],
            "PASS" if faithfulness.passed else "FAIL",
            [
                f"score={faithfulness.score:.2f}",
                f"sentiment={result.overall_sentiment}",
                f"conflicting={result.contains_conflicting_signals}",
            ],
        )
        assert faithfulness.passed, (
            f"Faithfulness check failed for {normal_case['id']}: "
            f"score={faithfulness.score:.2f} < threshold={faithfulness.threshold}"
        )
        if "expected_sentiment" in normal_case:
            assert result.overall_sentiment == normal_case["expected_sentiment"], (
                f"Sentiment mismatch for {normal_case['id']}: "
                f"expected={normal_case['expected_sentiment']!r}, "
                f"got={result.overall_sentiment!r}"
            )
        if "expected_conflicting" in normal_case:
            assert result.contains_conflicting_signals == normal_case["expected_conflicting"], (
                f"Conflicting signals mismatch for {normal_case['id']}: "
                f"expected={normal_case['expected_conflicting']}, "
                f"got={result.contains_conflicting_signals}"
            )

    @pytest.mark.adversarial
    @pytest.mark.ragas_ci
    def test_evaluate_adversarial(
        self,
        adversarial_case: dict[str, Any],
        summarizer: Summarizer,
        robustness_checker: RobustnessChecker,
        faithfulness_evaluator: FaithfulnessEvaluator,
    ):
        # When
        _log_input(
            adversarial_case["id"],
            adversarial_case["clean_text"],
            injection=adversarial_case["injection_template"],
        )
        robustness = robustness_checker.check(
            summarizer=summarizer,
            clean_text=adversarial_case["clean_text"],
            injection_template=adversarial_case["injection_template"],
        )
        faithfulness = faithfulness_evaluator.evaluate(
            source_text=adversarial_case["clean_text"],
            summary=robustness.adversarial_summary,
        )

        # Then
        _log_result(
            adversarial_case["id"],
            "PASS" if faithfulness.passed else "FAIL",
            [f"score={faithfulness.score:.2f}"],
        )
        assert faithfulness.passed, (
            f"Adversarial faithfulness failed for {adversarial_case['id']}: "
            f"score={faithfulness.score:.2f} < threshold={faithfulness.threshold}"
        )


class TestJudgeCalibration:
    @pytest.mark.ragas_ci
    def test_judge_calibration(
        self,
        judge_calibration_case: dict[str, Any],
        faithfulness_evaluator: FaithfulnessEvaluator,
    ):
        # When
        _log_input(judge_calibration_case["id"], judge_calibration_case["source_text"])
        faithfulness = faithfulness_evaluator.evaluate(
            source_text=judge_calibration_case["source_text"],
            summary=judge_calibration_case["summary"],
        )
        expected = judge_calibration_case["expected_faithfulness_pass"]

        # Then
        _log_result(
            judge_calibration_case["id"],
            "PASS" if faithfulness.passed == expected else "FAIL",
            [
                f"score={faithfulness.score:.2f}",
                f"expected_pass={expected}",
                f"actual_pass={faithfulness.passed}",
            ],
        )
        assert faithfulness.passed == expected, (
            f"Judge calibration failed for {judge_calibration_case['id']}: "
            f"expected passed={expected}, got passed={faithfulness.passed} "
            f"(score={faithfulness.score:.2f})"
        )


class TestPromptInjectionRobustness:
    @pytest.mark.adversarial
    def test_check(
        self,
        adversarial_case: dict[str, Any],
        summarizer: Summarizer,
        robustness_checker: RobustnessChecker,
    ):
        # When
        _log_input(
            adversarial_case["id"],
            adversarial_case["clean_text"],
            injection=adversarial_case["injection_template"],
        )
        result = robustness_checker.check(
            summarizer=summarizer,
            clean_text=adversarial_case["clean_text"],
            injection_template=adversarial_case["injection_template"],
        )

        # Then
        _log_result(
            adversarial_case["id"],
            "PASS" if result.passed else "FAIL",
            [
                f"robustness={'PASS' if result.passed else 'FAIL'}",
                f"baseline_sentiment={result.baseline_sentiment}",
                f"adversarial_sentiment={result.adversarial_sentiment}",
            ],
        )
        assert result.passed, (
            f"Robustness check failed for {adversarial_case['id']}: {result.details}"
        )


