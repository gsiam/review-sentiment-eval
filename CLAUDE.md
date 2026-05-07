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
npx markdownlint-cli docs/
lychee --include-fragments --root-dir . README.md CLAUDE.md 'docs/**/*.md'  # brew install lychee

# Tests
pytest -m unit              # Unit tests only (fast, no API)
pytest -m integration       # Integration tests (real API)

# Model selection (integration tests)
pytest -m integration --summarizer-model ollama/llama3.2 --judge-model ollama/mistral
pytest -m integration --summarizer-model ollama/llama3.2 --judge-model claude-sonnet-4-6

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

### Analysis Data

- `reports/aggregated.json` is the canonical data backing `docs/model-configuration-analysis.md`. It is tracked in git. Do not read it directly — run `scripts/model_doc_audit.py` instead to surface specific numbers without flooding the context window. Output includes per-case means with `fails N/3` / `flips N/3` / `wrong N/3` counts, pooled 6-run calibration (`wrong N/6` by judge type), unstable entries, and summary rows. Compare output against doc cells manually — the script dumps canonical values; discrepancies are spotted by eye.
- Run logs (`reports/*.log`, `reports/archive/`) are gitignored — large and already distilled into `aggregated.json`.

### Run Strategy for Config Analysis

Each model configuration gets **3 fresh runs** on the full dataset. Report scores as `mean [min–max]` per case, with threshold-failure counts: `fails N/3` (faithfulness), `flips N/3` (robustness), `wrong N/3` (calibration). §4 calibration pools 6 runs (SS+WS or SW+WW) → `wrong N/6`. Flag any case where max−min > 0.2 as unstable. Label logs distinctively (e.g. `reports/strong-strong-run1.log`). Single-run logs from before this convention are excluded from analysis tables.

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`, `@pytest.mark.ragas_ci`
