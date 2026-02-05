# Python Testing Conventions

## Test Structure

Use **Given-When-Then** comments:

```python
def test_threshold_boundary(self, evaluator):
    # Given
    evaluator.threshold = 0.5

    # When
    result = evaluator.evaluate(score=0.5)

    # Then
    assert result.passed is True
```

Skip "Given" if there's no meaningful setup beyond fixtures.

## Pytest Markers

Use markers to categorize tests:

- `unit` - Fast, no external dependencies
- `integration` - Real API/database calls
- `slow` - Tests that take significant time

```python
pytestmark = pytest.mark.unit  # All tests in file

@pytest.mark.integration  # Individual test
def test_real_api_call():
    ...
```

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

```python
# Good
class TestCheckStatic:
    def test_check_static(self):                # happy case
    def test_check_static_xml_injection(self):  # deviation

# Bad
class TestCheckStatic:
    def test_check_static_returns_result_for_clean_text(self):
    def test_check_static_should_detect_xml_injection(self):
```

### API/Integration Tests

The most useful info is the **HTTP method + path** (makes `curl` verification easy).

**Pattern:** `test_<METHOD>_<path> [<deviation>]`

```python
# Good
class TestBasketApi:
    def test_get_basket_id(self):             # happy case
    def test_get_basket_id_invalid(self):     # deviation
    def test_post_basket(self):

# Bad
class TestBasketApi:
    def test_get_basket_returns_200_and_json_for_valid_uuid(self):
```

### GUI Tests

The most useful info is the **interaction** (click, hover, submit, etc.).

**Pattern:** `test_<interaction> [<deviation>]`

```python
# Good
class TestBasketButton:
    def test_click(self):                # happy case (activated)
    def test_click_deactivated(self):    # deviation

# Bad
class TestBasketButton:
    def test_click_should_turn_into_quantity_field_when_activated(self):
```

**Class ordering:** simpler methods first, then complex ones, then private helpers.

## Test Organization

- **Keep test logic minimal** - complex logic belongs in the code being tested, not in tests
- **Two test layers**: unit (mocked, fast, free) and integration (real calls, slow)
