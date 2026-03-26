# Testing Conventions

## Test Structure

Use **Given-When-Then** comments to separate setup, action, and assertion:

```text
# Given
<setup>

# When
<action>

# Then
<assertion>
```

Skip `# Given` when there is no setup beyond what fixtures provide
(don't stack `# Given` directly above `# When` with nothing between them).

Add a docstring when the test's intent isn't obvious from its name alone.

## Test Naming

Follow these principles for concise, useful test names:

1. **Don't repeat the context** - class/file name already provides it
2. **Start with the most useful** - what helps find the cause fastest (varies by test type)
3. **Avoid filler words** - use `returns` not `should return`
4. **Don't specify the happy case** - only name deviations
5. **Don't state expectations** - assertions already do that

### Unit Tests

The most useful info is the **method being tested**.

**Pattern:** `test_<method> [<deviation>]`

```text
# Good
TestCheck:
    test_check                       # happy case
    test_check_sentiment_changed     # deviation

# Bad
TestCheck:
    test_check_returns_result_for_clean_text
    test_check_should_detect_sentiment_change
```

### API/Integration Tests

The most useful info is the **HTTP method + path** (makes `curl` verification easy).

**Pattern:** `test_<METHOD>_<path> [<deviation>]`

```text
# Good
TestBasketApi:
    test_get_basket_id             # happy case
    test_get_basket_id_invalid     # deviation
    test_post_basket

# Bad
TestBasketApi:
    test_get_basket_returns_200_and_json_for_valid_uuid
```

### GUI Tests

The most useful info is the **interaction** (click, hover, submit, etc.).

**Pattern:** `test_<interaction> [<deviation>]`

```text
# Good
TestBasketButton:
    test_click                # happy case (activated)
    test_click_deactivated    # deviation

# Bad
TestBasketButton:
    test_click_should_turn_into_quantity_field_when_activated
```

## Test Assertions

Prefer asserting the **full expected output** over multiple substring checks.
This catches formatting bugs that individual checks would miss.

```text
# Good: single assertion on the full output
assert "llm.request | model=ChatAnthropic | messages: [human: Hello]" in caplog.text

# Avoid: multiple substring assertions on the same output
assert "ChatAnthropic" in caplog.text
assert "human" in caplog.text
assert "Hello" in caplog.text
```

## Test Organization

- **Keep test logic minimal** - complex logic belongs in the code being tested, not in tests
- **Class ordering:** simpler methods first, then complex ones, then private helpers
- **Test ordering within a class:** happy path and core behavior first,
  boundary cases next, then defensive/edge cases last

## Test Independence

Tests must be fully self-contained — no shared mutable state, no execution
order dependencies. Accept duplicate setup (even duplicate API calls in
integration tests) rather than coupling tests through shared fixtures or
results from earlier tests.

Each test should check one concern. If a test needs four fixtures to verify
two independent failure modes, split it into two tests.

## Constants In Tests

Use production constants to reduce repeated setup values,
not to assert the same value back from the same source.

```text
# Good: de-duplicate setup
evaluator = FaithfulnessEvaluator(threshold=DEFAULT_THRESHOLD)

# Good: explicit contract assertion (catches default regressions)
assert evaluator.threshold == 0.7

# Avoid: tautological assertion
assert evaluator.threshold == DEFAULT_THRESHOLD
```

Rule of thumb:

- setup/arrange can use shared constants
- important external contracts (defaults, public outputs)
  should have at least one explicit literal assertion

## Test Categories

Use markers/tags to classify tests by intended use:

- `unit` - Fast, no external dependencies
- `integration` - Real API/database calls
- `e2e` - End-to-end flows
- `slow` - Tests that take significant time

Other examples: `smoke`, `visual`, `performance`. Choose categories that match the project's needs.
