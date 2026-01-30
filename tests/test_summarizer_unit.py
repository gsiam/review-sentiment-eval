"""Unit tests for Summarizer response parsing (no API calls)."""

from unittest.mock import patch

import pytest

from llm_eval.summarizer import Summarizer

pytestmark = pytest.mark.unit

# Realistic summary for tests where the summary content isn't being tested
VALID_SUMMARY = "The customer expressed satisfaction with the product quality and delivery time."


class TestParseResponseDirectJson:
    """Test parsing when the LLM returns pure JSON."""

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_pure_json(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Great product.", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_pure_json_with_whitespace(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '  \n{"summary": "Great product.", "sentiment": "positive"}\n  '

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"


class TestParseResponseCodeFence:
    """Test parsing when the LLM wraps JSON in code fences."""

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_json_code_fence(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```json\n{"summary": "Great product.", "sentiment": "positive"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_plain_code_fence(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```\n{"summary": "Great product.", "sentiment": "negative"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "negative"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_code_fence_with_preamble(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Here is the analysis:\n```json\n{"summary": "OK product.", "sentiment": "neutral"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "OK product."
        assert result["sentiment"] == "neutral"


class TestParseResponseBalancedBraces:
    """Test parsing when JSON is embedded in prose with nested braces."""

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_nested_braces_in_summary(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Includes {braces} inside", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Includes {braces} inside"
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_json_with_preamble_text(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Sure, here is the result: {"summary": "Nice.", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_json_with_trailing_text(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Nice.", "sentiment": "positive"}\nLet me know if you need more.'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["sentiment"] == "positive"


class TestParseResponseSentimentValidation:
    """Test sentiment normalization and validation."""

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_uppercase_sentiment_normalized(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "sentiment": "POSITIVE"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_whitespace_padded_sentiment_normalized(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "sentiment": " positive "}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["sentiment"] == "positive"


class TestValidateParsedRaisesOnInvalidSentiment:
    """Test that invalid or missing sentiment raises ValueError."""

    def test_missing_sentiment_raises(self):
        # Then
        with pytest.raises(ValueError, match="Missing required field"):
            # When
            Summarizer._validate_parsed({"summary": VALID_SUMMARY})

    @pytest.mark.parametrize("sentiment", [
        "somewhat_positive",
        "very_negative",
        "satisfied",
        "5",
    ])
    def test_invalid_sentiment_raises(self, sentiment):
        # Then
        with pytest.raises(ValueError, match="Invalid sentiment value"):
            # When
            Summarizer._validate_parsed({"summary": VALID_SUMMARY, "sentiment": sentiment})


class TestParseResponseFallback:
    """Test fallback when no valid JSON can be extracted."""

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_plain_text_fallback(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = "The customer was happy with the product overall."

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["sentiment"] == "neutral"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_invalid_json_fallback(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{summary: "missing quotes on key"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["sentiment"] == "neutral"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_json_missing_summary_key_fallback(self, mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["sentiment"] == "neutral"
