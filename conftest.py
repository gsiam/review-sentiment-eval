"""Root pytest configuration for LLM evaluation suite."""

import os

import pytest
from dotenv import load_dotenv


def pytest_configure(config):
    """Load environment variables before test collection."""
    load_dotenv()


def pytest_collection_modifyitems(config, items):
    """Skip tests requiring API key if not configured."""
    models = [config.getoption(name, None) for name in ("--summarizer-model", "--judge-model")]
    uses_anthropic = any(not (model or "").startswith("ollama/") for model in models)
    if uses_anthropic and not os.getenv("ANTHROPIC_API_KEY"):
        skip_marker = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set")
        for item in items:
            if "no_api_key" not in item.keywords:
                item.add_marker(skip_marker)
