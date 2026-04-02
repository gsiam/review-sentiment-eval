# CLAUDE.md - Project Context for AI Assistants

## Project Overview

LLM Evaluation Suite for testing summarization capabilities. Defaults to Claude Sonnet but supports injecting alternative LLMs. The project evaluates:

1. **Hallucinations** - Using Ragas Faithfulness metric (threshold 0.7)
2. **Prompt Injection Vulnerability** - Using adaptive behavioral analysis that compares baseline vs adversarial outputs

Main modules: `summarizer.py` (LLM calls + response parsing), `faithfulness_evaluator.py` (Ragas wrapper), `robustness_checker.py` (injection testing).

Active plan: `~/.claude/plans/llm-eval-model-agnostic.md`

## How to Run Things

```bash
# Setup
cd llm-eval
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # includes ruff, mypy, pytest-cov

# Environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Lint
ruff check src/ tests/

# Tests
pytest -m unit              # Unit tests only (fast, no API)
pytest -m integration       # Integration tests (real API)

# Model selection (integration tests)
pytest -m integration --summarizer-model ollama/llama3.2 --judge-model ollama/mistral
pytest -m integration --summarizer-model ollama/llama3.2 --judge-model claude-sonnet-4-20250514

# Coverage
pytest -m unit --cov=src/llm_eval --cov-branch

# Structured log output (integration tests)
pytest -m integration --log-cli-level=INFO
```

## Architecture Context

Before modifying core modules (`summarizer.py`, `faithfulness_evaluator.py`, `robustness_checker.py`, `logging_callback.py`) or their tests, read `docs/design-decisions.md`.
For project structure and architecture diagrams, see `README.md`.

## Standards

Refer to `.standards/general/`, `.standards/python/`,
`.standards/ai-workflow.md`, and `.standards/documentation.md` for general conventions.

**Before writing or modifying code, read the relevant `.standards/` files first.** Apply them from the start — don't write code then check compliance after.

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`, `@pytest.mark.ragas_ci`
