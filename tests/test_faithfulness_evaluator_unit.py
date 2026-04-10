"""Unit tests for FaithfulnessEvaluator (no API calls)."""

from unittest.mock import Mock, patch

import pytest

from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator

pytestmark = pytest.mark.unit

DEFAULT_THRESHOLD = FaithfulnessEvaluator.DEFAULT_THRESHOLD


@pytest.fixture()
def mock_async_anthropic():
    with patch("llm_eval.faithfulness_evaluator.AsyncAnthropic") as mock:
        yield mock


@pytest.fixture(autouse=True)
def _mock_llm_deps(mock_async_anthropic):
    """Prevent real LLM client construction and metric validation in all tests."""
    with (
        patch("llm_eval.faithfulness_evaluator.llm_factory"),
        patch("llm_eval.faithfulness_evaluator.Faithfulness"),
    ):
        yield


@pytest.fixture()
def evaluator():
    return FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)


class TestFaithfulnessEvaluatorLogic:
    def test_evaluate(self, evaluator):
        # Given
        passing_score = 0.9
        evaluator.faithfulness.score.return_value = Mock(value=passing_score)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary of original text",
        )

        # Then
        assert result.passed
        assert result.score == passing_score

    def test_evaluate_below_threshold(self, evaluator):
        # Given
        evaluator.faithfulness.score.return_value = Mock(value=0.5)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Hallucinated summary",
        )

        # Then
        assert not result.passed
        assert result.score == 0.5

    def test_evaluate_at_threshold(self, evaluator):
        # Given
        evaluator.faithfulness.score.return_value = Mock(value=DEFAULT_THRESHOLD)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert result.passed
        assert result.score == DEFAULT_THRESHOLD

    def test_evaluate_perfect_score(self, evaluator):
        # Given
        evaluator.faithfulness.score.return_value = Mock(value=1.0)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Perfect summary",
        )

        # Then
        assert result.passed
        assert result.score == 1.0

    def test_evaluate_zero_score(self, evaluator):
        # Given
        evaluator.faithfulness.score.return_value = Mock(value=0.0)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Completely hallucinated",
        )

        # Then
        assert not result.passed
        assert result.score == 0.0

    def test_evaluate_none_score(self, evaluator):
        # Given
        evaluator.faithfulness.score.return_value = Mock(value=None)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert not result.passed
        assert result.score == 0.0


class TestEvaluatorConfiguration:
    def test_init(self):
        # When
        evaluator = FaithfulnessEvaluator()

        # Then
        # Contract: default threshold is part of expected external behavior.
        assert evaluator.threshold == 0.7

    def test_init_custom_threshold(self):
        # Given
        custom_threshold = 0.85

        # When
        evaluator = FaithfulnessEvaluator(threshold=custom_threshold)

        # Then
        assert evaluator.threshold == custom_threshold

    def test_max_retries(self, mock_async_anthropic):
        # When
        FaithfulnessEvaluator()

        # Then
        mock_async_anthropic.assert_called_once_with(max_retries=6)
