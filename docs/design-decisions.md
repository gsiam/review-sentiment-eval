# Design Decisions

Implementation-level context for core modules. Read this before modifying
`summarizer.py`, `faithfulness_evaluator.py`, `robustness_checker.py`, `logging_callback.py`, or their tests.

---

## Adaptive Robustness Testing

Instead of fixed expected sentiments, we:

- Run clean text → get baseline `overall_sentiment`
- Inject opposite sentiment target
- Compare: if `overall_sentiment` changed → injection succeeded (fail)
- `contains_conflicting_signals` is logged but not used as pass/fail criteria

This avoids false positives from sentiment classification edge cases.
Adversarial cases also run Faithfulness to catch content manipulation
(e.g., injected text leaking into the summary). The judge plays no role
in robustness testing — `robustness_checker.check()` makes summarizer
calls only. A consequence: in any per-config robustness table, SS = SW
and WS = WW by construction. Robustness differences reflect the
summarizer only.

## Test Data Structure

Adversarial cases have `clean_text` + `injection_template` (not `source_text`). The injection is dynamically built with `{injected_sentiment}` placeholder.

## Two Test Layers

- Unit tests: Mock the summarizer, test logic only (fast, free)
- Integration tests: Real API calls (slow, costs money)

## Robust Response Parsing

`_parse_response` tries three strategies in order:

- Direct JSON parse (pure JSON output)
- Code-fenced JSON (` ```json ... ``` `)
- Balanced-brace extraction (JSON embedded in prose, handles nested `{}`)

Logs a warning on fallback to make parse failures visible. Current aggregation does not store parse status as a first-class field, so fallback counts are log-derived and should be treated as a methodology limitation until parse metadata is added to run records.

## Ragas LLM Integration

`Summarizer` uses `ChatAnthropic` (LangChain) for prompt/chain features. `FaithfulnessEvaluator` uses `ragas.llms.llm_factory` with an `AsyncAnthropic()` client because Ragas v0.4's `Faithfulness` metric (from `ragas.metrics.collections`) requires `InstructorBaseRagasLLM`, which only `llm_factory` returns. The evaluator calls `faithfulness.score()` directly (not `ragas.evaluate()`) because the collections `Faithfulness` inherits from `BaseMetric`, not `ragas.metrics.base.Metric`, and `evaluate()` rejects it with an isinstance check. `score()` runs `asyncio.run(ascore())` internally, which requires the async client. Both classes default to constructing their own LLM but accept a pre-built instance via `llm=` for testing and model swapping. `AsyncAnthropic` and `ChatAnthropic` are constructed with `max_retries=MAX_RETRIES` (currently 6) to handle transient 529 overload errors. Note: `conftest.py` fixtures bypass module constructors — they build LLM clients directly, so `MAX_RETRIES` must also be applied there explicitly.

## LLM Dependency Injection

Both `Summarizer` and `FaithfulnessEvaluator` accept an optional keyword-only `llm` parameter, falling back to the default if not provided. `Summarizer` accepts `BaseChatModel` (LangChain), `FaithfulnessEvaluator` accepts `InstructorBaseRagasLLM` (Ragas) — callers must provide the correct type for each. Types are imported under `TYPE_CHECKING` to avoid heavy runtime imports.

## LLM Logging

Two separate mechanisms because LangChain and Ragas use different LLM abstractions. `LLMLoggingCallback` (LangChain `BaseCallbackHandler`) handles Summarizer calls — logs model name at INFO, full messages at DEBUG. `RagasLoggingHandler` is a stateful class registered via `setup_ragas_logging` on instructor hooks (`completion:kwargs` / `completion:response`). It tracks state across the two Faithfulness LLM calls (statement extraction → NLI verdicts) to emit structured per-step log lines and a one-line faithfulness summary at INFO. Raw responses go to DEBUG. Handles both Anthropic (ToolUseBlock) and OpenAI/Ollama (ChatCompletion JSON) response formats. Logging is composed externally by the caller, not embedded in the core classes. Visible with `pytest --log-cli-level=INFO`.

## Split Sentiment Schema

The summarizer returns `overall_sentiment` (`positive`/`negative`/`neutral`) and `contains_conflicting_signals` (`true`/`false`). This gives downstream consumers a clear directional signal for routing/aggregation while separately flagging feedback that has both positive and negative aspects. The system prompt defines `overall_sentiment` as the customer's bottom-line takeaway (not a count of pros vs cons), with explicit tie-breaker rules: positive if broadly satisfied/would buy again, negative if broadly dissatisfied/would avoid, neutral only if no clear overall leaning. This operational definition is necessary — without it, ambiguous reviews (strong positive product + strong negative logistics) classify inconsistently as neutral.

## Ragas top_p Workaround

Ragas 0.4.3's `InstructorModelArgs` hardcodes `top_p: float = 0.1` — a non-optional Pydantic field that always serializes into the API call. The Anthropic provider path in `_map_provider_params` is a plain pass-through, so `top_p=0.1` is always forwarded. Anthropic deprecated `top_p` — models after Claude Opus 4.6 reject requests with both `temperature` and `top_p` (HTTP 400). Workaround: call `self.llm.model_args.pop("top_p", None)` after `llm_factory` returns. Applied in `FaithfulnessEvaluator.__init__` (guarded by `if llm is None` to avoid mutating injected clients) and in `conftest._make_judge_llm`. Remove once upstream fixes `_map_anthropic_params`. Bug filed: [vibrantlabsai/ragas#2674](https://github.com/vibrantlabsai/ragas/issues/2674).

## Two-Document Output Architecture

The evaluation suite produces two distinct outputs that must stay separate. The *verdict* — `docs/model-configuration-analysis.md` — holds prompts fixed and varies model backends. The *improvement map* — `docs/exploratory-findings.md` — identifies prompt-change hypotheses from failure patterns. Acting on any finding in the improvement map changes the system under test and requires a full re-run of the configuration analysis on the modified system. Mixing them in one document conflates two different systems under test.

## Faithfulness Metric Scope

Ragas Faithfulness rewards conservative summaries and can invert apparent quality rankings — stronger models that make ambitious derived claims score lower than weaker models that paraphrase safely. Two independent failure modes: (1) *precision-loss* cases (`magnitude_severity`, `magnitude_precision`, `scope_condition`, `spec_simplification`) share a structural gap: the softer claim remains factually true at the statement level, so decomposition-based metrics pass it. The gap is judge-dependent: `magnitude_precision` scores 1.00 across both judges in every run and cannot be reached by any threshold; the weak judge additionally misses `magnitude_severity` and `scope_condition` universally at 1.00; the strong judge is unstable on `magnitude_severity` (0.00–1.00) and scores `scope_condition` and `spec_simplification` at or below 0.70 in some runs. A complementary recall/coverage metric is required to address this class; threshold calibration alone cannot close it; (2) *threshold validity* holds only for classic-error types (`hallucinated`, `negation_flip`, `attribution_swap`, `number_swap`) where calibration shows a clear gap between faithful and unfaithful scores. Threshold placement and metric coverage are orthogonal arguments — a perfectly calibrated threshold still cannot detect precision-loss errors.

## Exploratory Testing as First-Class Output

Failure patterns visible only in per-run logs or cross-config comparisons — patterns that pass the gating threshold — are still actionable findings, documented in `docs/exploratory-findings.md`. Confidence levels: *medium* = 3+ independent confirming cases; *low-medium* = 1 case where the pattern is consistent with a well-documented model-behaviour characteristic (e.g., sarcasm blindness in small models); *low* = 1 case, no strong external prior, insufficient to act. When designing confidence rubrics for exploratory finding docs, explicitly state whether external prior evidence can raise confidence with fewer dataset cases — otherwise a finding invoking published literature will appear inconsistent with the rubric.

## Analysis Doc Visualisation Conventions

For data visualisations (charts with numeric data), use matplotlib PNG — not Mermaid. Mermaid's `xychart-beta` lacks label rotation and per-bar colour control; matplotlib gives precise control over colour encoding, axis labels, and threshold lines. (Mermaid remains appropriate for flowcharts, as per `.standards/documentation.md`.) For calibration score charts, colour encodes *correctness of judge behaviour*: faithful bars green if ≥ threshold, unfaithful bars green if < threshold (correctly caught) / red if ≥ threshold (miss). For heatmaps of score tables, use `matplotlib.colors.TwoSlopeNorm` centred at the threshold. For stacked bar chart legends, include per-type case count (`n=X`) in the legend label. Figure captions: label (e.g., "Fig. 2a.") + description in italics below the image; no "Generated by \<script\>" attribution. For tables with abbreviated column headers, place a key bullet list immediately above the table. Error bars are drawn unconditionally on all bars — stable bars get zero-height caps, not omitted marks. In a standalone document without section numbers, use simple ordinals for figures (Fig. 1, Fig. 2); do not invent prefixes from section abbreviations.

## Dataset Case ID Naming

Case IDs are descriptive, not sequential (e.g., `negative_sarcasm`, `positive_conflicting_conditional`). Descriptive names are self-documenting in test output, log lines, and analysis tables. Do not use `_001`-style suffixes as the primary differentiator — they degrade into opaque numbers as the dataset grows.

## Calibration Table Pooling

§4 of the analysis doc pools SS+WS (strong judge, 6 runs) and SW+WW (weak judge, 6 runs) into single mean columns. Calibration cases use pre-written summaries — the summariser plays no role, so per-config columns would imply summariser dependence where none exists. Do not reintroduce per-config columns or SS/WS labels in §4 prose, preamble, or captions. (§3.3 keeps per-config columns — it is comparing configuration behaviour, not calibrating the judge.)

## Calibration Verdict Granularity

Run-level instability and universal miss look similar in aggregate but require different remediations — run-level errors point to judge reliability or prompt tuning; a universal miss points to a metric gap. Do not collapse them under a single "judge wrong" framing, and do not use the term "false-flag". Canonical cases: `spec_simplification` (run-level false positives, strong judge), `magnitude_severity` (run-level false negatives, strong judge), `magnitude_precision` (universal miss, both judges). Definitions live in the §4 preamble of the analysis doc. The max−min > 0.2 threshold is pragmatic, not derived from first principles. For the current dataset, the minimum range among flagged entries is 0.25, so any cutoff from 0.20 to 0.25 produces the same flagged set. The more principled criterion is *threshold-straddling* (at least one run fails, at least one passes). The two criteria diverge for `negative_sarcasm` SW and `adversarial_markdown_table` SW — both always-passing but flagged by max−min > 0.2. If a borderline case with range ≈ 0.20 appears in a future dataset, decide explicitly which criterion applies — they are not the same.

## Judge vs Summariser Failure Mode Separation

`docs/exploratory-findings.md` documents failure modes in the *summariser* prompt — acting on any finding there changes the system under test and requires a full re-run. Judge-side failure modes (e.g., `spec_simplification` false positives via hyperliteral NLI) belong in `docs/model-configuration-analysis.md`. Do not move judge behaviour analysis into the exploratory findings document. See §4 of the analysis doc for the mechanism and data.
