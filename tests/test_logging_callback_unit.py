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
        assert "llm.request | model=ChatAnthropic | messages: [human: Hello]" in caplog.text

    def test_on_chat_model_start_multiple_messages(self, caplog):
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
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
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


class TestSetupRagasLogging:
    def test_setup_ragas_logging_request_hook(self, caplog):
        # Given
        mock_llm = Mock()
        hooks = {}

        def capture_hook(hook_name, handler):
            hooks[hook_name] = handler

        mock_llm.client.on = capture_hook
        setup_ragas_logging(mock_llm)

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
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

    def test_setup_ragas_logging_response_hook(self, caplog):
        # Given
        mock_llm = Mock()
        hooks = {}

        def capture_hook(hook_name, handler):
            hooks[hook_name] = handler

        mock_llm.client.on = capture_hook
        setup_ragas_logging(mock_llm)

        mock_response = Mock()
        mock_response.__str__ = lambda self: "Message(content='evaluated result')"

        # When
        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            hooks["completion:response"](mock_response)

        # Then
        assert "ragas.response | Message(content='evaluated result')" in caplog.text
