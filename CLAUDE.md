# CLAUDE.md - Project Context for AI Assistants

## Project Overview

LLM Evaluation Suite for testing summarization capabilities. Defaults to Claude Sonnet but supports injecting alternative LLMs. The project evaluates:

1. **Hallucinations** - Using Ragas Faithfulness metric (threshold 0.7)
2. **Prompt Injection Vulnerability** - Using adaptive behavioral analysis that compares baseline vs adversarial outputs

Main modules: `summarizer.py` (LLM calls + response parsing), `faithfulness_evaluator.py` (Ragas wrapper), `robustness_checker.py` (injection testing).

Plan (all steps complete; Deferred items remain): `~/.claude/plans/llm-eval-model-agnostic.md`

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

`docs/design-decisions.md` items use `##` headings in sentence case — not a numbered list. Anchor links work: `[Item title](docs/design-decisions.md#item-title)`. Do not reintroduce numbers or title case when adding new items.

`docs/design-decisions.md` is for *implemented* decisions only. Pre-implementation or deferred design (e.g., the behavioural canary, third-family judge experiment) lives in the plan's "Deferred / Open Discussion" section or the analysis doc's recommendations; items graduate to `design-decisions.md` only when the corresponding code lands.

The plan's "Deferred / Open Discussion" section is for genuinely open questions only. Before adding an item, confirm there is an actual unresolved question — not a decided constraint already documented in `docs/design-decisions.md` or the analysis doc's recommendations.

## Standards

Refer to `.standards/general/`, `.standards/python/`,
`.standards/ai-workflow.md`, and `.standards/documentation.md` for general conventions.

**Before writing or modifying code, read the relevant `.standards/` files first.** Apply them from the start — don't write code then check compliance after.

### Analysis Data

- `reports/aggregated.json` is the canonical data backing `docs/model-configuration-analysis.md`. It is tracked in git. Do not read it directly — run `scripts/model_doc_audit.py` instead to surface specific numbers without flooding the context window. Output includes per-case means with `fails N/3` / `flips N/3` / `wrong N/3` counts, pooled 6-run calibration (`wrong N/6` by judge type), unstable entries, and summary rows. Compare output against doc cells manually — the script dumps canonical values; discrepancies are spotted by eye.
- Run logs (`reports/*.log`, `reports/archive/`) are gitignored and mostly distilled into `aggregated.json`. Current exception: summarizer JSON parse fallback warnings are not stored as first-class aggregate fields, so any parse-failure count is log-derived until parse metadata is added to future run records.
- Any score value may appear in 2–4 locations simultaneously — table cells, §2a Notable bullets, §6 paragraphs, and `docs/exploratory-findings.md`. When updating a value anywhere, grep the full document for every occurrence before committing. A change also requires regenerating any figure that references the value (`scripts/generate_heatmap.py` and `scripts/generate_calibration_charts.py` both hardcode data — update the script AND regenerate the PNG). Run `python scripts/model_doc_audit.py` from the repo root to get canonical values before editing any cell.
- When a prose bullet and a table cell disagree on a numeric value, fix the prose to match the table — never the reverse. The table is derived from `reports/aggregated.json`; prose is written by hand and drifts. During any numeric migration, re-read all prose that references values in the affected table (§2a Notable bullets, §6 paragraphs, §6.1 inline enumerations) — a table pass alone will not catch prose divergences.

### Run Strategy for Config Analysis

Each model configuration gets **3 fresh runs** on the full dataset. Report scores as `mean [min–max]` per case, with threshold-failure counts: `fails N/3` (faithfulness), `flips N/3` (robustness), `wrong N/3` (calibration). §4 calibration pools 6 runs (SS+WS or SW+WW) → `wrong N/6`. Flag any case where max−min > 0.2 as unstable. Annotation bold/label rules: `fails **N/3**` — bold when N ≥ 1, no annotation at all when N = 0 (faith columns); `flips **N/3**` — always shown, bold when N ≥ 1, `flips 0/3` unbolded (robustness columns); `wrong **N/3**` — bold when N ≥ 1, `wrong 0/3` unbolded (calibration columns). Label logs distinctively (e.g. `reports/strong-strong-run1.log`). Single-run logs from before this convention are excluded from analysis tables. Mean is used over median because with n=3, median discards two of the three data points. "Universal miss" = `wrong 3/3` per-config (or `wrong 6/6` in §4 pooled); the §4 preamble must explicitly identify the N/6 pooling — without this, pooled counts read as per-run N/3 values.

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`, `@pytest.mark.ragas_ci`

### Model IDs

- `claude-sonnet-4-6` and other dateless 4.6+ IDs are **pinned snapshots** — Anthropic does not update weights or configuration under the same ID. Pre-4.6 dateless IDs (e.g. `claude-sonnet-4-5`) ARE mutable aliases that resolve to the latest dated snapshot.
- Observable behaviour can still shift for any pinned ID due to provider-side infrastructure (serving layer, safety classifiers, sampling logic) — not weight replacement.
