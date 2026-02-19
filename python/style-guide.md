# Python Style Guide

## Code Organization

- Use **dataclasses** for structured return types (not tuples or dicts)
- Type hints on all function signatures (parameters + return types)

## Documentation

- **Google-style docstrings** with `Args:` and `Returns:` sections for public APIs
- One-line docstrings for simple helper methods

## Logging

Use `logging.getLogger(__name__)` - not print statements.
