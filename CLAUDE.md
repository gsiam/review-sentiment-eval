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

## Architecture Notes

```text
llm-eval/
├── src/llm_eval/
│   ├── summarizer.py          # Summarization + sentiment + conflict detection
│   ├── faithfulness_evaluator.py  # Ragas Faithfulness wrapper
│   ├── robustness_checker.py  # Adaptive injection testing
│   └── logging_callback.py   # LLM request/response logging
├── tests/
│   ├── conftest.py            # Fixtures, parametrization, model selection CLI
│   ├── test_summarization.py  # Integration tests (real API)
│   ├── test_summarizer_unit.py     # Unit tests for response parsing
│   ├── test_robustness_checker_unit.py
│   ├── test_faithfulness_evaluator_unit.py
│   └── test_logging_callback_unit.py
└── data/
    └── test_dataset.json      # 6 normal + 2 adversarial cases
```

### Key Design Decisions

1. **Adaptive Robustness Testing**: Instead of fixed expected sentiments, we:
   - Run clean text → get baseline `overall_sentiment`
   - Inject opposite sentiment target
   - Compare: if `overall_sentiment` changed → injection succeeded (fail)
   - `contains_conflicting_signals` is logged but not used as pass/fail criteria

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

5. **Ragas LLM Integration**: `Summarizer` uses `ChatAnthropic` (LangChain) for prompt/chain features. `FaithfulnessEvaluator` uses `ragas.llms.llm_factory` with an `AsyncAnthropic()` client because Ragas v0.4's `Faithfulness` metric (from `ragas.metrics.collections`) requires `InstructorBaseRagasLLM`, which only `llm_factory` returns. The evaluator calls `faithfulness.score()` directly (not `ragas.evaluate()`) because the collections `Faithfulness` inherits from `BaseMetric`, not `ragas.metrics.base.Metric`, and `evaluate()` rejects it with an isinstance check. `score()` runs `asyncio.run(ascore())` internally, which requires the async client. Both classes default to constructing their own LLM but accept a pre-built instance via `llm=` for testing and model swapping.

6. **LLM Dependency Injection**: Both `Summarizer` and `FaithfulnessEvaluator` accept an optional keyword-only `llm` parameter, falling back to the default if not provided. `Summarizer` accepts `BaseChatModel` (LangChain), `FaithfulnessEvaluator` accepts `InstructorBaseRagasLLM` (Ragas) — callers must provide the correct type for each. Types are imported under `TYPE_CHECKING` to avoid heavy runtime imports.

7. **LLM Logging**: Two separate mechanisms because LangChain and Ragas use different LLM abstractions. `LLMLoggingCallback` (LangChain `BaseCallbackHandler`) handles Summarizer calls — logs model name at INFO, full messages at DEBUG. `RagasLoggingHandler` is a stateful class registered via `setup_ragas_logging` on instructor hooks (`completion:kwargs` / `completion:response`). It tracks state across the two Faithfulness LLM calls (statement extraction → NLI verdicts) to emit structured per-step log lines and a one-line faithfulness summary at INFO. Raw responses go to DEBUG. Handles both Anthropic (ToolUseBlock) and OpenAI/Ollama (ChatCompletion JSON) response formats. Logging is composed externally by the caller, not embedded in the core classes. Visible with `pytest --log-cli-level=INFO`.

8. **Split Sentiment Schema**: The summarizer returns `overall_sentiment` (`positive`/`negative`/`neutral`) and `contains_conflicting_signals` (`true`/`false`). This gives downstream consumers a clear directional signal for routing/aggregation while separately flagging feedback that has both positive and negative aspects. The system prompt defines `overall_sentiment` as the customer's bottom-line takeaway (not a count of pros vs cons), with explicit tie-breaker rules: positive if broadly satisfied/would buy again, negative if broadly dissatisfied/would avoid, neutral only if no clear overall leaning. This operational definition is necessary — without it, ambiguous reviews (strong positive product + strong negative logistics) classify inconsistently as neutral.

## Standards

Refer to `.standards/general/`, `.standards/python/`,
`.standards/ai-workflow.md`, and `.standards/documentation.md` for general conventions.

**Before writing or modifying code, read the relevant `.standards/` files first.** Apply them from the start — don't write code then check compliance after.

### Project-Specific

- Python 3.10+
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.adversarial`, `@pytest.mark.ragas_ci`

### Dependencies

- `anthropic` for async Anthropic client (used by Ragas `llm_factory` — must be `AsyncAnthropic`, not sync)
- `langchain-anthropic` for Claude API (used by Summarizer)
- `ragas` for Faithfulness metric (v0.4+ collections API)
- `pytest` for testing
- `langchain-ollama` for local Ollama models (optional, install with `pip install -e ".[local]"`)
