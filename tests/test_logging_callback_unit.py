"""Unit tests for LLM logging callbacks (no API calls)."""

import logging
from unittest.mock import Mock
from uuid import uuid4

import pytest

from llm_eval.logging_callback import LLMLoggingCallback, setup_ragas_logging

pytestmark = pytest.mark.unit

LOGGER_NAME = "llm_eval.logging_callback"


class TestOnChatModelStart:
    def test_on_chat_model_start(self, caplog):
        # Given
        callback = LLMLoggingCallback()
        serialized = {
            "id": ["langchain", "chat_models", "anthropic", "ChatAnthropic"],
        }
        messages = [[Mock(type="human", content="Hello")]]

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            callback.on_chat_model_start(serialized, messages, run_id=uuid4())

        # Then
        assert "llm.request | model=ChatAnthropic" in caplog.text
        assert "Hello" not in caplog.text

    def test_on_chat_model_start_debug(self, caplog):
        # Given
        callback = LLMLoggingCallback()
        serialized = {"id": ["langchain", "chat_models", "ChatAnthropic"]}
        messages = [
            [
                Mock(type="system", content="Be helpful"),
                Mock(type="human", content="Summarize this"),
            ]
        ]

        # When
        with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
            callback.on_chat_model_start(serialized, messages, run_id=uuid4())

        # Then
        assert (
            "llm.request | model=ChatAnthropic"
            " | messages: [system: Be helpful, human: Summarize this]"
            in caplog.text
        )


class TestOnLlmEnd:
    def test_on_llm_end(self, caplog):
        # Given
        callback = LLMLoggingCallback()
        response = Mock()
        response.generations = [[Mock(text="The answer is 42")]]

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            callback.on_llm_end(response, run_id=uuid4())

        # Then
        assert "llm.response | text: The answer is 42" in caplog.text

    def test_on_llm_end_empty_generations(self, caplog):
        """Guard: logs warning instead of crashing on empty generations."""
        # Given
        callback = LLMLoggingCallback()
        response = Mock()
        response.generations = []

        # When
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            callback.on_llm_end(response, run_id=uuid4())

        # Then
        assert "llm.response | empty generations" in caplog.text


def _setup_hooks(mock_llm: Mock) -> dict:
    """Wire setup_ragas_logging and return the captured hooks dict."""
    hooks: dict = {}

    def capture_hook(hook_name: str, handler: object) -> None:
        hooks[hook_name] = handler

    mock_llm.client.on = capture_hook
    setup_ragas_logging(mock_llm)
    return hooks


def _make_anthropic_tool_use_response(payload: dict) -> Mock:
    """Build a mock Anthropic Message with a single ToolUseBlock."""
    block = Mock()
    block.type = "tool_use"
    block.input = payload
    response = Mock()
    response.content = [block]
    del response.choices  # Mock auto-creates attributes; remove so OpenAI path won't match
    return response


class TestSetupRagasLogging:
    def test_on_request(self, caplog):
        # Given
        hooks = _setup_hooks(Mock())

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:kwargs"](
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "test prompt"}],
            )

        # Then
        assert "ragas.request | model=claude-sonnet-4-20250514" in caplog.text
        assert "test prompt" not in caplog.text

    def test_on_request_debug(self, caplog):
        # Given
        hooks = _setup_hooks(Mock())

        # When
        with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
            hooks["completion:kwargs"](
                model="claude-sonnet-4-20250514",
                messages=[{"role": "user", "content": "test prompt"}],
            )

        # Then
        assert (
            "ragas.request | model=claude-sonnet-4-20250514"
            " | messages: [{'role': 'user', 'content': 'test prompt'}]"
            in caplog.text
        )

    def test_on_response_statements(self, caplog):
        # Given
        hooks = _setup_hooks(Mock())
        response = _make_anthropic_tool_use_response(
            {"statements": ["The product was okay.", "Shipping was slow."]},
        )

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:response"](response)

        # Then
        assert (
            "ragas.statements | ['The product was okay.', 'Shipping was slow.']"
            in caplog.text
        )

    def test_on_response_nli_verdicts(self, caplog):
        # Given
        hooks = _setup_hooks(Mock())
        response = _make_anthropic_tool_use_response(
            {
                "statements": [
                    {"statement": "The product was okay.", "reason": "supported", "verdict": 1},
                    {"statement": "Shipping was fast.", "reason": "contradicted", "verdict": 0},
                ],
            },
        )

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:response"](response)

        # Then
        assert "ragas.verdicts | faithful=1/2" in caplog.text

    def test_on_response_faithfulness_summary(self, caplog):
        """Emits a one-line summary after both pipeline calls."""
        # Given
        hooks = _setup_hooks(Mock())
        stmt_response = _make_anthropic_tool_use_response(
            {"statements": ["stmt1", "stmt2", "stmt3"]},
        )
        nli_response = _make_anthropic_tool_use_response(
            {
                "statements": [
                    {"statement": "stmt1", "reason": "ok", "verdict": 1},
                    {"statement": "stmt2", "reason": "ok", "verdict": 1},
                    {"statement": "stmt3", "reason": "no", "verdict": 0},
                ],
            },
        )

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:response"](stmt_response)
            hooks["completion:response"](nli_response)

        # Then
        assert "ragas.faithfulness | statements=3 | faithful=2/3 | score=0.67" in caplog.text

    def test_on_response_openai(self, caplog):
        """OpenAI/Ollama JSON-mode response."""
        # Given
        hooks = _setup_hooks(Mock())
        response = Mock()
        response.content = []
        choice = Mock()
        choice.message.content = '{"statements": ["stmt1"]}'
        response.choices = [choice]

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:response"](response)

        # Then
        assert 'ragas.response | text: {"statements": ["stmt1"]}' in caplog.text

    def test_on_response_debug(self, caplog):
        """Raw response object at DEBUG only."""
        # Given
        hooks = _setup_hooks(Mock())
        response = _make_anthropic_tool_use_response(
            {"statements": ["stmt1"]},
        )
        response.__str__ = lambda self: "Message(raw dump)"

        # When
        with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
            hooks["completion:response"](response)

        # Then
        assert "ragas.response | Message(raw dump)" in caplog.text
