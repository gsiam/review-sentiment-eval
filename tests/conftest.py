"""Test fixtures for LLM evaluation suite."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from llm_eval.constants import DEFAULT_MODEL, MAX_RETRIES
from llm_eval.faithfulness_evaluator import FaithfulnessEvaluator
from llm_eval.logging_callback import LLMLoggingCallback, setup_ragas_logging
from llm_eval.robustness_checker import RobustnessChecker
from llm_eval.summarizer import Summarizer

# Suppress noisy HTTP client logs when using --log-cli-level=INFO
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

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

    return ChatAnthropic(model=model_spec, temperature=0, callbacks=callbacks, max_retries=MAX_RETRIES)


def _make_judge_llm(model_spec: str) -> InstructorBaseRagasLLM:
    """Return an InstructorBaseRagasLLM for the given spec, with logging hooks attached."""
    from ragas.llms import llm_factory

    if model_spec.startswith("ollama/"):
        model_name = model_spec.removeprefix("ollama/")
        from openai import AsyncOpenAI

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        client = AsyncOpenAI(base_url=base_url, api_key="ollama")
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
            client=AsyncAnthropic(max_retries=MAX_RETRIES),
            temperature=0,
        )
        # Ragas 0.4.3 hardcodes top_p=0.1; Anthropic rejects requests with
        # both temperature and top_p (HTTP 400). Remove until upstream fix.
        llm.model_args.pop("top_p", None)

    setup_ragas_logging(llm)
    return llm


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
    if "normal_case" in metafunc.fixturenames:
        dataset_path = DATA_DIR / "test_dataset.json"
        with open(dataset_path) as f:
            data = json.load(f)
        normal_cases = [
            c for c in data["test_cases"]
            if not c["is_adversarial"] and not c["is_judge_calibration"]
        ]
        metafunc.parametrize(
            "normal_case",
            normal_cases,
            ids=[case["id"] for case in normal_cases],
        )

    if "judge_calibration_case" in metafunc.fixturenames:
        dataset_path = DATA_DIR / "test_dataset.json"
        with open(dataset_path) as f:
            data = json.load(f)
        calibration_cases = [c for c in data["test_cases"] if c["is_judge_calibration"]]
        metafunc.parametrize(
            "judge_calibration_case",
            calibration_cases,
            ids=[case["id"] for case in calibration_cases],
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
