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

## Test Organization

- **Keep test logic minimal** - complex logic belongs in the code being tested, not in tests
- **Two test layers**: unit (mocked, fast, free) and integration (real calls, slow)
