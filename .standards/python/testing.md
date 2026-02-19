# Python Testing Conventions

## Pytest Markers

Use markers to categorize tests:

```python
pytestmark = pytest.mark.unit  # All tests in file

@pytest.mark.integration  # Individual test
def test_real_api_call():
    ...
```

## Example

```python
def test_threshold_boundary(self, evaluator):
    # Given
    evaluator.threshold = 0.5

    # When
    result = evaluator.evaluate(score=0.5)

    # Then
    assert result.passed is True
```
