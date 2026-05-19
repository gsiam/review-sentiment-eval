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

## Loading scripts via importlib

When a test file loads a standalone script via `importlib.util.spec_from_file_location`
(because the script is not on the Python path), do not use bare `assert` to
check the spec — it fires as a collection-phase `AssertionError` with no message
if the path moves. Use `pytest.fail()` with the path for actionable diagnostics:

```python
spec = importlib.util.spec_from_file_location("my_script", MODULE_PATH)
if spec is None or spec.loader is None:
    pytest.fail(f"Could not load {MODULE_PATH}")

module = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(module)
except ImportError as exc:
    pytest.fail(f"Could not import {MODULE_PATH}: {exc}")
```
