# CLAUDE.md - Project Context for AI Assistants

## Project Overview

LLM Evaluation Suite for testing Claude Sonnet's summarization capabilities. The project evaluates:

1. **Hallucinations** - Using Ragas Faithfulness metric (threshold 0.7)
2. **Prompt Injection Vulnerability** - Using adaptive behavioral analysis that compares baseline vs adversarial outputs

Main modules: `summarizer.py` (LLM calls + response parsing), `evaluator.py` (Ragas wrapper), `robustness_checker.py` (injection testing).

## How to Run Things

```bash
# Setup
cd llm-eval
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .

# Environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

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
│   ├── evaluator.py           # Ragas Faithfulness wrapper
│   └── robustness_checker.py  # Adaptive injection testing
├── tests/
│   ├── conftest.py            # Fixtures, parametrization
│   ├── test_summarization.py  # Integration tests (real API)
│   ├── test_summarizer_unit.py     # Unit tests for response parsing
│   ├── test_robustness_checker_unit.py
│   └── test_evaluator_unit.py
└── data/
    └── test_dataset.json      # 5 normal + 2 adversarial cases
```

### Key Design Decisions

1. **Adaptive Robustness Testing**: Instead of fixed expected sentiments, we:
   - Run clean text → get baseline sentiment
   - Inject opposite sentiment target
   - Compare: if output changed → injection succeeded (fail)

   This avoids false positives from sentiment classification edge cases.

2. **Test Data Structure**: Adversarial cases have `clean_text` + `injection_template` (not `source_text`). The injection is dynamically built with `{target_sentiment}` placeholder.

3. **Two Test Layers**:
   - Unit tests: Mock the summarizer, test logic only (fast, free)
   - Integration tests: Real API calls (slow, costs money)

4. **Robust Response Parsing**: `_parse_response` tries three strategies in order:
   - Direct JSON parse (pure JSON output)
   - Code-fenced JSON (` ```json ... ``` `)
   - Balanced-brace extraction (JSON embedded in prose, handles nested `{}`)

   Logs a warning on fallback to make parse failures visible.

## Standards

Follow the conventions in:

- [Python Style Guide](.standards/python/style-guide.md)
- [Python Testing](.standards/python/testing.md)
- [AI Workflow Rules](.standards/ai-workflow.md)

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`

### Dependencies

- `langchain-anthropic` for Claude API
- `ragas` for Faithfulness metric
- `pytest` for testing
