"""Faithfulness evaluator using Ragas metrics."""

from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness


@dataclass
class FaithfulnessResult:
    """Result from faithfulness evaluation."""

    score: float
    passed: bool
    threshold: float


class FaithfulnessEvaluator:
    """Evaluator for summarization faithfulness using Ragas.

    Faithfulness measures whether claims in the summary are supported
    by the source text (i.e., no hallucinations).
    """

    DEFAULT_THRESHOLD = 0.7

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        threshold: float = DEFAULT_THRESHOLD,
    ):
        """Initialize the faithfulness evaluator.

        Args:
            model: The Claude model to use for evaluation.
            threshold: Minimum faithfulness score to pass (0.0 to 1.0).
        """
        self.threshold = threshold
        self.llm = LangchainLLMWrapper(ChatAnthropic(model=model, temperature=0))
        self.faithfulness = Faithfulness(llm=self.llm)

    def evaluate(self, source_text: str, summary: str) -> FaithfulnessResult:
        """Evaluate faithfulness of a summary against source text.

        Args:
            source_text: The original customer feedback.
            summary: The generated summary to evaluate.

        Returns:
            FaithfulnessResult with score and pass/fail status.
        """
        sample = SingleTurnSample(
            user_input="Summarize this customer feedback",
            response=summary,
            retrieved_contexts=[source_text],
        )

        dataset = EvaluationDataset(samples=[sample])

        results = evaluate(
            dataset=dataset,
            metrics=[self.faithfulness],
        )

        score = results.scores[0].get("faithfulness", 0.0)
        if score is None:
            score = 0.0

        return FaithfulnessResult(
            score=score,
            passed=score >= self.threshold,
            threshold=self.threshold,
        )
