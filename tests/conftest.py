"""Test fixtures for LLM evaluation suite."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from llm_eval.constants import DEFAULT_MODEL
from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator
from llm_eval.logging_callback import LLMLoggingCallback, setup_ragas_logging
from llm_eval.robustness_checker import RobustnessChecker
from llm_eval.summarizer import Summarizer

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from ragas.llms import InstructorBaseRagasLLM


DATA_DIR = Path(__file__).parent.parent / "data"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add CLI options for model selection."""
    parser.addoption(
        "--summarizer-model",
        default=DEFAULT_MODEL,
        help=f"Model for Summarizer (default: {DEFAULT_MODEL}). Use 'ollama/<model>' for local.",
    )
    parser.addoption(
        "--judge-model",
        default=DEFAULT_MODEL,
        help=f"Model for FaithfulnessEvaluator judge (default: {DEFAULT_MODEL}). Use 'ollama/<model>' for local.",
    )


def _make_summarizer_llm(model_spec: str) -> BaseChatModel:
    """Return a BaseChatModel for the given spec, with logging callback attached."""
    callbacks = [LLMLoggingCallback()]

    if model_spec.startswith("ollama/"):
        model_name = model_spec.removeprefix("ollama/")
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model_name, temperature=0, callbacks=callbacks)

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=model_spec, temperature=0, callbacks=callbacks)


def _make_judge_llm(model_spec: str) -> InstructorBaseRagasLLM:
    """Return an InstructorBaseRagasLLM for the given spec, with logging hooks attached."""
    from ragas.llms import llm_factory

    if model_spec.startswith("ollama/"):
        model_name = model_spec.removeprefix("ollama/")
        from openai import OpenAI

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        client = OpenAI(base_url=base_url, api_key="ollama")
        llm = llm_factory(
            model=model_name,
            provider="openai",
            client=client,
            temperature=0,
        )
    else:
        from anthropic import AsyncAnthropic

        llm = llm_factory(
            model=model_spec,
            provider="anthropic",
            client=AsyncAnthropic(),
            temperature=0,
        )

    setup_ragas_logging(llm)
    return llm


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
def summarizer(request: pytest.FixtureRequest) -> Summarizer:
    """Create a shared Summarizer with the configured model."""
    model_spec = request.config.getoption("--summarizer-model")
    llm = _make_summarizer_llm(model_spec)
    return Summarizer(llm=llm)


@pytest.fixture(scope="session")
def faithfulness_evaluator(request: pytest.FixtureRequest) -> FaithfulnessEvaluator:
    """Create a shared FaithfulnessEvaluator with the configured judge model."""
    model_spec = request.config.getoption("--judge-model")
    llm = _make_judge_llm(model_spec)
    return FaithfulnessEvaluator(
        llm=llm,
        threshold=FaithfulnessEvaluator.DEFAULT_THRESHOLD,
    )


@pytest.fixture(scope="session")
def robustness_checker() -> RobustnessChecker:
    return RobustnessChecker()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
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
