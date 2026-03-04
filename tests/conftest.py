"""Test fixtures for LLM evaluation suite."""

import json
from pathlib import Path
from typing import Any

import pytest

from llm_eval.summarizer import Summarizer
from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator
from llm_eval.robustness_checker import RobustnessChecker


DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture(scope="session")
def evaluation_dataset() -> list[dict[str, Any]]:
    """Load test dataset from JSON file."""
    dataset_path = DATA_DIR / "test_dataset.json"
    with open(dataset_path) as f:
        data = json.load(f)
    return data["test_cases"]


@pytest.fixture(scope="session")
def normal_cases(evaluation_dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to only normal (non-adversarial) test cases."""
    return [case for case in evaluation_dataset if not case["is_adversarial"]]


@pytest.fixture(scope="session")
def adversarial_cases(evaluation_dataset: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter to only adversarial test cases."""
    return [case for case in evaluation_dataset if case["is_adversarial"]]


@pytest.fixture(scope="session")
def summarizer() -> Summarizer:
    """Create a shared Summarizer instance."""
    return Summarizer()


@pytest.fixture(scope="session")
def faithfulness_evaluator() -> FaithfulnessEvaluator:
    """Create a shared FaithfulnessEvaluator instance."""
    return FaithfulnessEvaluator(threshold=FaithfulnessEvaluator.DEFAULT_THRESHOLD)


@pytest.fixture(scope="session")
def robustness_checker() -> RobustnessChecker:
    """Create a shared RobustnessChecker instance."""
    return RobustnessChecker()


def pytest_generate_tests(metafunc):
    """Dynamically parametrize tests based on test dataset."""
    if "test_case" in metafunc.fixturenames:
        dataset_path = DATA_DIR / "test_dataset.json"
        with open(dataset_path) as f:
            data = json.load(f)
        test_cases = data["test_cases"]
        metafunc.parametrize(
            "test_case",
            test_cases,
            ids=[case["id"] for case in test_cases],
        )

    if "normal_case" in metafunc.fixturenames:
        dataset_path = DATA_DIR / "test_dataset.json"
        with open(dataset_path) as f:
            data = json.load(f)
        normal_cases = [c for c in data["test_cases"] if not c["is_adversarial"]]
        metafunc.parametrize(
            "normal_case",
            normal_cases,
            ids=[case["id"] for case in normal_cases],
        )

    if "adversarial_case" in metafunc.fixturenames:
        dataset_path = DATA_DIR / "test_dataset.json"
        with open(dataset_path) as f:
            data = json.load(f)
        adversarial_cases = [c for c in data["test_cases"] if c["is_adversarial"]]
        metafunc.parametrize(
            "adversarial_case",
            adversarial_cases,
            ids=[case["id"] for case in adversarial_cases],
        )
