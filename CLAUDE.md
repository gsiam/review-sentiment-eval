# CLAUDE.md - Project Context for AI Assistants

## Project Overview

LLM Evaluation Suite for testing Claude Sonnet's summarization capabilities. The project evaluates:

1. **Hallucinations** - Using Ragas Faithfulness metric (threshold 0.7)
2. **Prompt Injection Vulnerability** - Using adaptive behavioral analysis that compares baseline vs adversarial outputs

Main modules: `summarizer.py` (LLM calls + response parsing), `faithfulness_evaluator.py` (Ragas wrapper), `robustness_checker.py` (injection testing).

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
pytest -v --log-cli-level=WARNING  # Show warnings (e.g. parse failures)
```

## Architecture Notes

```text
llm-eval/
├── src/llm_eval/
│   ├── summarizer.py          # Claude Sonnet summarization + sentiment
│   ├── faithfulness_evaluator.py  # Ragas Faithfulness wrapper
│   └── robustness_checker.py  # Adaptive injection testing
├── tests/
│   ├── conftest.py            # Fixtures, parametrization
│   ├── test_summarization.py  # Integration tests (real API)
│   ├── test_summarizer_unit.py     # Unit tests for response parsing
│   ├── test_robustness_checker_unit.py
│   └── test_faithfulness_evaluator_unit.py
└── data/
    └── test_dataset.json      # 5 normal + 2 adversarial cases
```

### Key Design Decisions

1. **Adaptive Robustness Testing**: Instead of fixed expected sentiments, we:
   - Run clean text → get baseline sentiment
   - Inject opposite sentiment target
   - Compare: if output changed → injection succeeded (fail)

   This avoids false positives from sentiment classification edge cases.
   Adversarial cases also run Faithfulness to catch content manipulation
   (e.g., injected text leaking into the summary).

2. **Test Data Structure**: Adversarial cases have `clean_text` + `injection_template` (not `source_text`). The injection is dynamically built with `{injected_sentiment}` placeholder.

3. **Two Test Layers**:
   - Unit tests: Mock the summarizer, test logic only (fast, free)
   - Integration tests: Real API calls (slow, costs money)

4. **Robust Response Parsing**: `_parse_response` tries three strategies in order:
   - Direct JSON parse (pure JSON output)
   - Code-fenced JSON (` ```json ... ``` `)
   - Balanced-brace extraction (JSON embedded in prose, handles nested `{}`)

   Logs a warning on fallback to make parse failures visible.

5. **Ragas LLM Integration**: `Summarizer` uses `ChatAnthropic` (LangChain) for prompt/chain features. `FaithfulnessEvaluator` uses `ragas.llms.llm_factory` with a raw `Anthropic()` client because Ragas v0.4's `Faithfulness` metric (from `ragas.metrics.collections`) requires `InstructorBaseRagasLLM`, which only `llm_factory` returns. The two libraries each demand their own LLM type.

## Standards

Refer to `.standards/general/`, `.standards/python/`,
`.standards/ai-workflow.md`, and `.standards/documentation.md` for general conventions.

**Before writing or modifying code, read the relevant `.standards/` files first.** Apply them from the start — don't write code then check compliance after.

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`

### Dependencies

- `anthropic` for raw Anthropic client (used by Ragas `llm_factory`)
- `langchain-anthropic` for Claude API (used by Summarizer)
- `ragas` for Faithfulness metric (v0.4+ collections API)
- `pytest` for testing
