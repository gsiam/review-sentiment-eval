"""Unit tests for FaithfulnessEvaluator (no API calls)."""

from unittest.mock import Mock, patch

import pytest

from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator

pytestmark = pytest.mark.unit

DEFAULT_THRESHOLD = FaithfulnessEvaluator.DEFAULT_THRESHOLD


class TestFaithfulnessEvaluatorLogic:
    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_evaluate(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        passing_score = 0.9
        mock_evaluate.return_value = Mock(
            scores=[{"faithfulness": passing_score}]
        )
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary of original text",
        )

        # Then
        assert result.passed
        assert result.score == passing_score

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_evaluate_below_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.5}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

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
    def test_evaluate_at_threshold(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": DEFAULT_THRESHOLD}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

        # When
        result = evaluator.evaluate(
            source_text="Original text",
            summary="Summary",
        )

        # Then
        assert result.passed
        assert result.score == DEFAULT_THRESHOLD

    @patch("llm_eval.faithfulness_evaluator.evaluate")
    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_evaluate_none_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": None}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

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
    def test_evaluate_missing_key(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

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
    def test_evaluate_custom_threshold(
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
    def test_evaluate_perfect_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 1.0}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

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
    def test_evaluate_zero_score(
        self, _mock_chat, _mock_wrapper, mock_evaluate
    ):
        # Given
        mock_evaluate.return_value = Mock(scores=[{"faithfulness": 0.0}])
        evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

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
    def test_init(self, _mock_chat, _mock_wrapper):
        # Given
        # When
        evaluator = FaithfulnessEvaluator()

        # Then
        # Contract: default threshold is part of expected external behavior.
        assert evaluator.threshold == 0.7

    @patch("llm_eval.faithfulness_evaluator.LangchainLLMWrapper")
    @patch("llm_eval.faithfulness_evaluator.ChatAnthropic")
    def test_init_custom_threshold(self, _mock_chat, _mock_wrapper):
        # Given
        custom_threshold = 0.85

        # When
        evaluator = FaithfulnessEvaluator(threshold=custom_threshold)

        # Then
        assert evaluator.threshold == 0.85
