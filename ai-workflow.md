# AI Workflow Rules

## Development Approach

- **Small diffs** - targeted changes, don't rewrite entire files
- **TDD flow** - write/update tests first, then implement to make them pass
- **Ask before adding dependencies** - check if existing tools can solve the problem first

## Code Changes

**Don't over-engineer:**

- Only make changes that are directly requested or clearly necessary
- Don't add features or "improvements" beyond what was asked
- A bug fix doesn't need surrounding code cleaned up

**Avoid backwards-compatibility hacks:**

- Don't rename unused variables to `_var`
- Don't add `# removed` comments for deleted code
- Don't re-export types "for compatibility" (if you move something, update the imports)
- If something is unused, delete it completely
