# Python Style Guide

## Clarity

- **Eliminate double negatives** - Write `passed = match` not `passed = not changed`
- **Remove redundant fields** - If one field is always `not other`, keep only one
- **Avoid ambiguous names** - If a name could be interpreted multiple ways in context, choose a more specific one

## Code Organization

- Use **dataclasses** for structured return types (not tuples or dicts)
- Type hints on all function signatures (parameters + return types)

## Documentation

- **Google-style docstrings** with `Args:` and `Returns:` sections for public APIs
- Private helpers: add a docstring only when the name and type signature don't fully describe the behavior (e.g., non-obvious side effects, routing logic, edge cases). Skip it when the docstring would just restate the name.

## Logging

Use `logging.getLogger(__name__)` - not print statements.
