# Design Decisions

Implementation-level context for core modules. Read this before modifying
`summarizer.py`, `faithfulness_evaluator.py`, `robustness_checker.py`, `logging_callback.py`, or their tests.

---

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
