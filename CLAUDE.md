# CLAUDE.md - Project Context for AI Assistants

## Project Overview

LLM Evaluation Suite for testing Claude Sonnet's summarization capabilities. The project evaluates:

1. **Hallucinations** - Using Ragas Faithfulness metric (threshold 0.7)
2. **Prompt Injection Vulnerability** - Using adaptive behavioral analysis that compares baseline vs adversarial outputs

Main modules: `summarizer.py` (LLM calls), `evaluator.py` (Ragas wrapper), `robustness_checker.py` (injection testing).

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
pytest -m unit              # Unit tests only (~0.05s, no API)
pytest -m integration       # Integration tests (~3-5 min, real API)
pytest -v --html=reports/test_report.html  # All tests with HTML report
```

## Architecture Notes

```
llm-eval/
├── src/llm_eval/
│   ├── summarizer.py        # Claude Sonnet summarization + sentiment
│   ├── evaluator.py         # Ragas Faithfulness wrapper
│   └── robustness_checker.py # Adaptive injection testing
├── tests/
│   ├── conftest.py          # Fixtures, parametrization
│   ├── test_summarization.py      # Integration tests (real API)
│   ├── test_robustness_checker_unit.py  # Unit tests (mocked)
│   └── test_evaluator_unit.py     # Unit tests (mocked)
├── data/
│   └── test_dataset.json    # 5 normal + 2 adversarial cases
└── reports/                 # HTML test reports
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

## Conventions

### Code Style

- Python 3.10+
- Use dataclasses for result types
- Type hints everywhere
- Docstrings with Args/Returns sections

### Test Style

- Use Given-When-Then structure (just keywords, no explanations)
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`
- Keep test logic minimal - complex logic goes in the checker/evaluator classes

### Dependencies

- `langchain-anthropic` for Claude API
- `ragas` for Faithfulness metric
- `pytest-html` for reports

## AI Workflow Rules

1. **Read before edit**: Always read files before modifying them
2. **Prefer small diffs**: Make targeted changes, don't rewrite entire files
3. **Ask before adding dependencies**: Check if existing tools can solve the problem
4. **Run unit tests after changes**: `pytest -m unit` is fast, use it often
5. **Keep tests readable**: Logic in checker/evaluator, tests just call and assert

## Current Focus / TODOs

- [x] Implement adaptive robustness testing
- [x] Add unit tests with mocks for RobustnessChecker and FaithfulnessEvaluator
- [x] Add Given-When-Then structure to unit tests
- [x] Add Given-When-Then structure to integration tests
- [ ] Check coverage of unit tests
- [ ] Check coverage of integration tests
- [ ] Refactor `TestEndToEnd` tests to remove logic from there
- [ ] Check whether we're happy with the convention for test naming
- [ ] Consider whether we need `reports`
- [ ] Improve diagrams (maybe make them with NanoBanana)
- [ ] Add logging
- [ ] Fix Ragas deprecation warnings (use `ragas.metrics.collections` instead)
  - [ ] use `llm_factory` instead of `LangchainLLMWrapper`
- [ ] Add a **Custom Judge** (using LangChain) that checks a specific business rule.
  - *The Rule:* "Summaries must never use the first person ('I think...')."
  - *The Implementation:* Write a simple custom evaluator in Python.
  - *Why:* It proves I can build my own metrics (Level 2) when the off-the-shelf libraries (Ragas) aren't enough.
- [ ] Discuss in the README current limitations with the current evaluation solution.
- [ ] Consider adding more adversarial injection patterns
