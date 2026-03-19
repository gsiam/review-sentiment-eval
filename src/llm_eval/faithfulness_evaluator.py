"""Faithfulness evaluator using Ragas metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from anthropic import AsyncAnthropic
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

from llm_eval.constants import DEFAULT_MODEL

if TYPE_CHECKING:
    from ragas.llms import InstructorBaseRagasLLM


@dataclass
class FaithfulnessResult:
    score: float
    passed: bool
    threshold: float


class FaithfulnessEvaluator:
    """Measures whether claims in the summary are supported by the source text."""

    DEFAULT_THRESHOLD = 0.7

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        threshold: float = DEFAULT_THRESHOLD,
        *,
        llm: InstructorBaseRagasLLM | None = None,
    ):
        self.threshold = threshold
        self.llm = llm or llm_factory(
            model=model,
            provider="anthropic",
            client=AsyncAnthropic(),
            temperature=0,
        )
        self.faithfulness = Faithfulness(llm=self.llm)

    def evaluate(self, source_text: str, summary: str) -> FaithfulnessResult:
        result = self.faithfulness.score(
            user_input="Summarize this customer feedback",
            response=summary,
            retrieved_contexts=[source_text],
        )
        score = float(result.value) if result.value is not None else 0.0
        return FaithfulnessResult(
            score=score,
            passed=score >= self.threshold,
            threshold=self.threshold,
        )
