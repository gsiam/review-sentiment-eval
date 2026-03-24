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
            [f"score={faithfulness.score:.2f}", f"sentiment={result.sentiment}"],
        )
        assert faithfulness.passed, (
            f"Faithfulness check failed for {normal_case['id']}: "
            f"score={faithfulness.score:.2f} < threshold={faithfulness.threshold}"
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
                f"baseline={result.baseline_sentiment}",
                f"adversarial={result.adversarial_sentiment}",
            ],
        )
        assert result.passed, (
            f"Robustness check failed for {adversarial_case['id']}: {result.details}"
        )


