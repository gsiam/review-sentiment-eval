"""Unit tests for Summarizer response parsing (no API calls)."""

from unittest.mock import patch

import pytest

from llm_eval.summarizer import Summarizer

pytestmark = pytest.mark.unit

VALID_SUMMARY = "The customer expressed satisfaction with the product quality and delivery time."


class TestParseResponseDirectJson:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Great product.", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_whitespace_padded(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '  \n{"summary": "Great product.", "sentiment": "positive"}\n  '

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_nested_braces_in_summary(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Includes {braces} inside", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Includes {braces} inside"
        assert result["sentiment"] == "positive"


class TestParseResponseCodeFence:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_code_fence(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```json\n{"summary": "Great product.", "sentiment": "positive"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Great product."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_plain_code_fence(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '```\n{"summary": "Product was defective and support was unhelpful.", "sentiment": "negative"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Product was defective and support was unhelpful."
        assert result["sentiment"] == "negative"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_code_fence_with_preamble(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Here is the analysis:\n```json\n{"summary": "OK product.", "sentiment": "neutral"}\n```'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "OK product."
        assert result["sentiment"] == "neutral"


class TestParseResponseEmbeddedJson:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_with_preamble(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = 'Sure, here is the result: {"summary": "Nice.", "sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_with_trailing_text(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Nice.", "sentiment": "positive"}\nLet me know if you need more.'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == "Nice."
        assert result["sentiment"] == "positive"


class TestParseResponseSentimentValidation:
    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_uppercase_sentiment(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "sentiment": "POSITIVE"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["sentiment"] == "positive"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_whitespace_padded_sentiment(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"summary": "Review.", "sentiment": " positive "}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["sentiment"] == "positive"


class TestValidateParsedRaisesOnInvalidSentiment:
    def test_validate_parsed_missing_sentiment(self):
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
    def test_validate_parsed_invalid_sentiment(self, sentiment):
        # Then
        with pytest.raises(ValueError, match="Invalid sentiment value"):
            # When
            Summarizer._validate_parsed({"summary": VALID_SUMMARY, "sentiment": sentiment})


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
        assert result["sentiment"] == "neutral"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_invalid_json_fallback(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{summary: "missing quotes on key"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["sentiment"] == "neutral"

    @patch("llm_eval.summarizer.ChatAnthropic")
    def test_parse_response_json_missing_summary_key_fallback(self, _mock_chat):
        # Given
        summarizer = Summarizer()
        raw = '{"sentiment": "positive"}'

        # When
        result = summarizer._parse_response(raw)

        # Then
        assert result["summary"] == raw
        assert result["sentiment"] == "neutral"
