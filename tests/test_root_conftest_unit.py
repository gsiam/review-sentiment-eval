"""Unit tests for the API-key skip hook in the root conftest."""

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest

from llm_eval.constants import DEFAULT_MODEL

pytestmark = pytest.mark.unit

MODULE_PATH = Path(__file__).resolve().parents[1] / "conftest.py"


def load_root_conftest() -> ModuleType:
    spec = importlib.util.spec_from_file_location("root_conftest", MODULE_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not load {MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as exc:
        pytest.fail(f"Could not import {MODULE_PATH}: {exc}")
    return module


root_conftest = load_root_conftest()


def make_config(summarizer_model: str, judge_model: str) -> Mock:
    options = {"--summarizer-model": summarizer_model, "--judge-model": judge_model}
    config = Mock()
    config.getoption.side_effect = lambda name, default=None: options.get(name, default)
    return config


def make_item() -> Mock:
    item = Mock()
    item.keywords = {}
    return item


def test_pytest_collection_modifyitems_local_models_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = make_config("ollama/llama3.2", "ollama/mistral")
    item = make_item()

    # When
    root_conftest.pytest_collection_modifyitems(config, [item])

    # Then
    item.add_marker.assert_not_called()


def test_pytest_collection_modifyitems_claude_judge_without_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = make_config("ollama/llama3.2", DEFAULT_MODEL)
    item = make_item()

    # When
    root_conftest.pytest_collection_modifyitems(config, [item])

    # Then
    item.add_marker.assert_called_once()


def test_pytest_collection_modifyitems_claude_models_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    config = make_config(DEFAULT_MODEL, DEFAULT_MODEL)
    item = make_item()

    # When
    root_conftest.pytest_collection_modifyitems(config, [item])

    # Then
    item.add_marker.assert_not_called()
