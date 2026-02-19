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

Skip "Given" if there's no meaningful setup beyond fixtures.

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

## Test Organization

- **Keep test logic minimal** - complex logic belongs in the code being tested, not in tests
- **Class ordering:** simpler methods first, then complex ones, then private helpers

## Test Categories

Use markers/tags to classify tests by intended use:

- `unit` - Fast, no external dependencies
- `integration` - Real API/database calls
- `e2e` - End-to-end flows
- `slow` - Tests that take significant time

Other examples: `smoke`, `visual`, `performance`. Choose categories that match the project's needs.
