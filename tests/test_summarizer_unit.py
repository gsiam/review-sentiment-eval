"""Unit tests for Summarizer response parsing (no API calls)."""

from unittest.mock import patch

import pytest

from llm_eval.constants import DEFAULT_MODEL
from llm_eval.summarizer import Summarizer

pytestmark = pytest.mark.unit

VALID_SUMMARY = "The customer expressed satisfaction with the product quality and delivery time."


class TestParseResponseDirectJson:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Great product.", "overall_sentiment": "positive", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_whitespace_padded(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '  \n{"summary": "Great product.", "overall_sentiment": "positive", "contains_conflicting_signals": false}\n  '

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_nested_braces_in_summary(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Includes {braces} inside", "overall_sentiment": "positive", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Includes {braces} inside"
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False


class TestParseResponseCodeFence:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_code_fence(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```json\n{"summary": "Great product.", "overall_sentiment": "positive", "contains_conflicting_signals": false}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_plain_code_fence(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```\n{"summary": "Product was defective and support was unhelpful.", "overall_sentiment": "negative", "contains_conflicting_signals": false}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Product was defective and support was unhelpful."
        assert result["overall_sentiment"] == "negative"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_code_fence_with_preamble(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Here is the analysis:\n```json\n{"summary": "OK product.", "overall_sentiment": "neutral", "contains_conflicting_signals": false}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "OK product."
        assert result["overall_sentiment"] == "neutral"
        assert result["contains_conflicting_signals"] is False


class TestParseResponseEmbeddedJson:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_with_preamble(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Sure, here is the result: {"summary": "Nice.", "overall_sentiment": "positive", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_with_trailing_text(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Nice.", "overall_sentiment": "positive", "contains_conflicting_signals": false}\nLet me know if you need more.'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["overall_sentiment"] == "positive"
        assert result["contains_conflicting_signals"] is False


class TestParseResponseSentimentValidation:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_uppercase_sentiment(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "overall_sentiment": "POSITIVE", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["overall_sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_whitespace_padded_sentiment(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "overall_sentiment": " positive ", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["overall_sentiment"] == "positive"


class TestValidateParsed:
    def test_validate_parsed_missing_overall_sentiment(self):
        with pytest.raises(ValueError, match="Missing required field: 'overall_sentiment'"):
            Summarizer._validate_parsed({
                "summary": VALID_SUMMARY,
                "contains_conflicting_signals": False,
            })

    def test_validate_parsed_missing_contains_conflicting_signals(self):
        with pytest.raises(ValueError, match="Missing required field: 'contains_conflicting_signals'"):
            Summarizer._validate_parsed({
                "summary": VALID_SUMMARY,
                "overall_sentiment": "positive",
            })

    @pytest.mark.parametrize("sentiment", [
        "somewhat_positive",
        "very_negative",
        "satisfied",
        "mixed",
        "5",
    ])
    def test_validate_parsed_invalid_sentiment(self, sentiment):
        with pytest.raises(ValueError, match="Invalid overall_sentiment value"):
            Summarizer._validate_parsed({
                "summary": VALID_SUMMARY,
                "overall_sentiment": sentiment,
                "contains_conflicting_signals": False,
            })

    def test_validate_parsed_non_boolean_conflicting_signals(self):
        with pytest.raises(ValueError, match="Invalid contains_conflicting_signals value"):
            Summarizer._validate_parsed({
                "summary": VALID_SUMMARY,
                "overall_sentiment": "positive",
                "contains_conflicting_signals": "yes",
            })


class TestParseResponseFallback:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_plain_text_fallback(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = "The customer was happy with the product overall."

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["overall_sentiment"] == "neutral"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_invalid_json_fallback(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{summary: "missing quotes on key"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["overall_sentiment"] == "neutral"
        assert result["contains_conflicting_signals"] is False

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_missing_summary_key_fallback(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"overall_sentiment": "positive", "contains_conflicting_signals": false}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["overall_sentiment"] == "neutral"
        assert result["contains_conflicting_signals"] is False


class TestSummarizerInit:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_max_retries(self, mock_chat):
        # When
        Summarizer()

        # Then
        mock_chat.assert_called_once_with(
            model=DEFAULT_MODEL,
            temperature=0,
            max_retries=6,
        )
