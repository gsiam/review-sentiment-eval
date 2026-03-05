# Python Testing Conventions

## Pytest Markers

Use markers to categorize tests:

```python
pytestmark = pytest.mark.unit  # All tests in file

@pytest.mark.integration  # Individual test
def test_real_api_call():
    ...
```

## Fixtures for Shared Mocks

Use `autouse` fixtures to patch infrastructure dependencies (API clients,
wrappers) that every test needs suppressed. Use named fixtures for mocks
that tests need to configure.

```python
@pytest.fixture(autouse=True)
def _mock_llm_deps():
    """Prevent real client construction in all tests."""
    with (
        patch("mymodule.ChatAnthropic"),
        patch("mymodule.LangchainLLMWrapper"),
    ):
        yield


@pytest.fixture()
def mock_evaluate():
    with patch("mymodule.evaluate") as mock_eval:
        yield mock_eval
```

- `autouse` + `_` prefix: active for all tests, not referenced by name
- Named fixture: requested explicitly by tests that need the mock object
- Prefer this over `@patch` decorators stacked on every method

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
