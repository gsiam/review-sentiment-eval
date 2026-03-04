"""Unit tests for FaithfulnessEvaluator (no API calls)."""

from unittest.mock import Mock, patch

import pytest

from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator, FaithfulnessResult

pytestmark = pytest.mark.unit


class TestFaithfulnessResult:
    def test_result_with_passing_score(self):
        # Given
        score = 0.85
        threshold = 0.7

        # When
        result = FaithfulnessResult(score=score, passed=True, threshold=threshold)

        # Then
        assert result.score == 0.85
        assert result.passed
        assert result.threshold == 0.7

    def test_result_with_failing_score(self):
        # Given
        score = 0.5
        threshold = 0.7

        # When
        result = FaithfulnessResult(score=score, passed=False, threshold=threshold)

        # Then
        assert result.score == 0.5
        assert not result.passed

    def test_result_at_threshold(self):
        # Given
        score = 0.7
        threshold = 0.7

        # When
        result = FaithfulnessResult(score=score, passed=True, threshold=threshold)

        # Then
        assert result.passed


class TestFaithfulnessEvaluatorLogic:
    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_passes_when_score_above_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.9}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary of original text",
        )

        # Then
        assert result.passed
        assert result.score == 0.9
        assert result.threshold == 0.7

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_fails_when_score_below_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.5}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Hallucinated summary",
        )

        # Then
        assert not result.passed
        assert result.score == 0.5

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_passes_at_exact_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.7}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert result.passed
        assert result.score == 0.7

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_handles_none_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": None}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert not result.passed
        assert result.score == 0.0

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_handles_missing_faithfulness_key(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert not result.passed
        assert result.score == 0.0

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_custom_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.85}])
        evaluator = FaithfulnessEvaluator(threshold=0.9)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert not result.passed
        assert result.threshold == 0.9

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_perfect_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 1.0}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Perfect summary",
        )

        # Then
        assert result.passed
        assert result.score == 1.0

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_zero_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.0}])
        evaluator = FaithfulnessEvaluator(threshold=0.7)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Completely hallucinated",
        )

        # Then
        assert not result.passed
        assert result.score == 0.0


class TestEvaluatorConfiguration:
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_default_threshold(self, _mock_chat, _mock_wrapper):
        # Given
        # When
        evaluator = FaithfulnessEvaluator()

        # Then
        assert evaluator.threshold == 0.7

    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_custom_threshold_stored(self, _mock_chat, _mock_wrapper):
        # Given
        custom_threshold = 0.85

        # When
        evaluator = FaithfulnessEvaluator(threshold=custom_threshold)

        # Then
        assert evaluator.threshold == 0.85
