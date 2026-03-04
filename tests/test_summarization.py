"""Test harness for summarization evaluation (integration tests - real API)."""

from typing import Any

import pytest

from llm_eval.summarizer import Summarizer
from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator
from llm_eval.robustness_checker import RobustnessChecker

pytestmark = pytest.mark.integration


class TestSummarizationFaithfulness:
    @pytest.mark.ragas_ci
    def test_evaluate(
        self,
        normal_case: dict[str, Any],
        summarizer: Summarizer,
        faithfulness_evaluator: FaithfulnessEvaluator,
    ):
        # When
        result = summarizer.summarize(normal_case["source_text"])
        faithfulness = faithfulness_evaluator.evaluate(
            source_text=normal_case["source_text"],
            summary=result.summary,
        )

        # Then
        assert faithfulness.passed, (
            f"Faithfulness check failed for {normal_case['id']}: "
            f"score={faithfulness.score:.2f} < threshold={faithfulness.threshold}"
        )


class TestPromptInjectionRobustness:
    @pytest.mark.adversarial
    def test_check(
        self,
        adversarial_case: dict[str, Any],
        summarizer: Summarizer,
        robustness_checker: RobustnessChecker,
    ):
        # When
        result = robustness_checker.check(
            summarizer=summarizer,
            clean_text=adversarial_case["clean_text"],
            injection_template=adversarial_case["injection_template"],
        )

        # Then
        assert result.passed, (
            f"Robustness check failed for {adversarial_case['id']}: {result.details}"
        )


class TestEndToEnd:
    @pytest.mark.ragas_ci
    @pytest.mark.adversarial
    def test_pipeline(
        self,
        evaluation_dataset: list[dict[str, Any]],
        summarizer: Summarizer,
        faithfulness_evaluator: FaithfulnessEvaluator,
        robustness_checker: RobustnessChecker,
    ):
        # When
        results = []
        for case in evaluation_dataset:
            if case["is_adversarial"]:
                # Adversarial: robustness check + faithfulness on adversarial summary
                robustness = robustness_checker.check(
                    summarizer=summarizer,
                    clean_text=case["clean_text"],
                    injection_template=case["injection_template"],
                )
                # Check faithfulness against clean text (not adversarial text)
                faithfulness = faithfulness_evaluator.evaluate(
                    source_text=case["clean_text"],
                    summary=robustness.adversarial_summary,
                )
                results.append({
                    "id": case["id"],
                    "is_adversarial": True,
                    "baseline_sentiment": robustness.baseline_sentiment,
                    "adversarial_sentiment": robustness.adversarial_sentiment,
                    "robustness_passed": robustness.passed,
                    "robustness_details": robustness.details,
                    "faithfulness_score": faithfulness.score,
                    "faithfulness_passed": faithfulness.passed,
                })
            else:
                # Normal: run faithfulness check
                summary_result = summarizer.summarize(case["source_text"])
                faithfulness = faithfulness_evaluator.evaluate(
                    source_text=case["source_text"],
                    summary=summary_result.summary,
                )
                results.append({
                    "id": case["id"],
                    "is_adversarial": False,
                    "summary": summary_result.summary,
                    "detected_sentiment": summary_result.sentiment,
                    "expected_sentiment": case["expected_sentiment"],
                    "faithfulness_score": faithfulness.score,
                    "faithfulness_passed": faithfulness.passed,
                })

        # Then
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY REPORT")
        print("=" * 80)

        for r in results:
            if r["is_adversarial"]:
                passed = r["robustness_passed"] and r["faithfulness_passed"]
                status = "PASS" if passed else "FAIL"
                print(f"\n{r['id']} [ADVERSARIAL]: {status}")
                print(f"  Baseline: {r['baseline_sentiment']}, Adversarial: {r['adversarial_sentiment']}")
                print(f"  Robustness: {'PASS' if r['robustness_passed'] else 'FAIL'}")
                print(f"  Faithfulness: {r['faithfulness_score']:.2f} ({'PASS' if r['faithfulness_passed'] else 'FAIL'})")
                if not r["robustness_passed"]:
                    print(f"    Details: {r['robustness_details']}")
            else:
                status = "PASS" if r["faithfulness_passed"] else "FAIL"
                print(f"\n{r['id']}: {status}")
                print(f"  Summary: {r['summary'][:100]}...")
                print(f"  Sentiment: detected={r['detected_sentiment']}, expected={r['expected_sentiment']}")
                print(f"  Faithfulness: {r['faithfulness_score']:.2f} ({'PASS' if r['faithfulness_passed'] else 'FAIL'})")

        print("\n" + "=" * 80)

        total = len(results)
        passed = sum(
            1 for r in results
            if (r["is_adversarial"] and r["robustness_passed"] and r["faithfulness_passed"])
            or (not r["is_adversarial"] and r["faithfulness_passed"])
        )
        print(f"OVERALL: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
        print("=" * 80 + "\n")

        failed_cases = [
            r for r in results
            if (r["is_adversarial"] and (not r["robustness_passed"] or not r["faithfulness_passed"]))
            or (not r["is_adversarial"] and not r["faithfulness_passed"])
        ]
        assert not failed_cases, (
            f"{len(failed_cases)} test case(s) failed: "
            f"{[r['id'] for r in failed_cases]}"
        )

    def test_summarize_sentiment_accuracy(
        self,
        normal_cases: list[dict[str, Any]],
        summarizer: Summarizer,
    ):
        # Given
        correct = 0
        total = len(normal_cases)

        # When
        for case in normal_cases:
            result = summarizer.summarize(case["source_text"])

            detected = result.sentiment.lower()
            expected = case["expected_sentiment"].lower()

            if detected == expected:
                correct += 1
            elif {detected, expected} <= {"neutral", "mixed"}:
                correct += 1

        # Then
        accuracy = correct / total if total > 0 else 0
        print(f"\nSentiment Detection Accuracy: {correct}/{total} ({100*accuracy:.1f}%)")

        assert accuracy >= 0.6, (
            f"Sentiment detection accuracy too low: {accuracy:.1%} < 60%"
        )
