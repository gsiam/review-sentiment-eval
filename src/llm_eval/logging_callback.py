"""Logging callbacks for LLM request/response observability.

Visible with: ``pytest --log-cli-level=INFO``
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


class LLMLoggingCallback(BaseCallbackHandler):
    """LangChain callback that logs LLM requests and responses.

    Attach via ``callbacks=[LLMLoggingCallback()]`` on a ``ChatAnthropic``
    instance or pass in the ``invoke`` config.
    """

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Log model name, message roles, and content."""
        model_name = serialized.get("id", ["unknown"])[-1]
        logger.info("llm.request | model=%s", model_name)
        for batch in messages:
            parts = [f"{msg.type}: {msg.content}" for msg in batch]
            logger.debug(
                "llm.request | model=%s | messages: [%s]",
                model_name,
                ", ".join(parts),
            )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Log response text."""
        if not response.generations or not response.generations[0]:
            logger.warning("llm.response | empty generations")
            return
        text = response.generations[0][0].text
        logger.info("llm.response | text: %s", text)


class RagasLoggingHandler:
    """Stateful handler for Ragas instructor hooks.

    Tracks state across the two Faithfulness LLM calls (statement extraction
    and NLI verdicts) to emit a one-line summary after each pipeline run.

    Raw responses go to DEBUG; extracted payloads go to INFO.
    """

    def __init__(self) -> None:
        self._statement_count: int | None = None

    def on_request(self, **kwargs: Any) -> None:
        model = kwargs.get("model", "unknown")
        logger.info("ragas.request | model=%s", model)
        messages = kwargs.get("messages", [])
        logger.debug("ragas.request | model=%s | messages: %s", model, messages)

    def on_response(self, response: Any) -> None:
        logger.debug("ragas.response | %s", response)

        # Anthropic: Message with content blocks (tool_use mode)
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use":
                self._handle_tool_use(block.input)
                return
            if getattr(block, "type", None) == "text":
                logger.info("ragas.response | text: %s", block.text)
                return

        # OpenAI/Ollama: ChatCompletion with choices (JSON mode)
        for choice in getattr(response, "choices", []):
            content = getattr(getattr(choice, "message", None), "content", None)
            if content:
                logger.info("ragas.response | text: %s", content)
                return

    def _handle_tool_use(self, payload: dict[str, Any]) -> None:
        """Route Anthropic ToolUseBlock payloads to the appropriate log format.

        Ragas Faithfulness uses two sequential tool calls:
        1. Statement extraction — ``{"statements": ["str", ...]}``
        2. NLI verdicts — ``{"statements": [{"statement": ..., "verdict": 0|1}, ...]}``

        Distinguishes them by checking whether list items are strings or dicts.
        After the NLI call, emits a faithfulness summary line.
        """
        statements = payload.get("statements")
        if not isinstance(statements, list) or not statements:
            logger.info("ragas.response | tool_use: %s", payload)
            return

        if isinstance(statements[0], str):
            self._statement_count = len(statements)
            logger.info("ragas.statements | %s", statements)
        elif isinstance(statements[0], dict):
            num_faithful = sum(1 for s in statements if s.get("verdict") == 1)
            total = len(statements)
            score = num_faithful / total if total else 0.0
            verdicts = [
                {"statement": s.get("statement", "")[:80], "verdict": s.get("verdict")}
                for s in statements
            ]
            logger.info(
                "ragas.verdicts | faithful=%d/%d | %s",
                num_faithful,
                total,
                verdicts,
            )
            logger.info(
                "ragas.faithfulness | statements=%d | faithful=%d/%d | score=%.2f",
                self._statement_count or total,
                num_faithful,
                total,
                score,
            )
            self._statement_count = None
        else:
            logger.info("ragas.response | tool_use: %s", payload)


def setup_ragas_logging(llm: Any) -> None:
    """Register request/response logging hooks on a Ragas InstructorLLM.

    Uses the underlying ``instructor.Instructor.on()`` API to attach hooks
    for ``completion:kwargs`` (request) and ``completion:response``.

    Args:
        llm: An ``InstructorLLM`` instance (from ``llm_factory``).
    """
    handler = RagasLoggingHandler()
    llm.client.on("completion:kwargs", handler.on_request)
    llm.client.on("completion:response", handler.on_response)
