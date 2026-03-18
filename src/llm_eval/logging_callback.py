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
        for batch in messages:
            parts = [f"{msg.type}: {msg.content}" for msg in batch]
            logger.info(
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


def setup_ragas_logging(llm: Any) -> None:
    """Register request/response logging hooks on a Ragas InstructorLLM.

    Uses the underlying ``instructor.Instructor.on()`` API to attach hooks
    for ``completion:kwargs`` (request) and ``completion:response``.

    Args:
        llm: An ``InstructorLLM`` instance (from ``llm_factory``).
    """

    def _log_request(**kwargs: Any) -> None:
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        logger.info("ragas.request | model=%s | messages: %s", model, messages)

    def _log_response(response: Any) -> None:
        logger.info("ragas.response | %s", response)

    llm.client.on("completion:kwargs", _log_request)
    llm.client.on("completion:response", _log_response)
