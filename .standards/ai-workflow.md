# AI Workflow Rules

## Development Approach

- **Small diffs** - targeted changes, don't rewrite entire files
- **TDD flow** - write/update tests first, then implement to make them pass
- **Ask before adding dependencies** - check if existing tools can solve the problem first
- **Check for linting errors after changes** - review diagnostics in code, CI workflows, config files, and fix issues before moving on

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

## Doc Verification

**State the goal alongside mechanical checks** — a verification prompt that only lists "find and check these strings" can confirm edits landed but cannot catch replacements that are technically correct and still fail the communication objective. Include one sentence on what an external reader should now be able to do that they couldn't before.

**Verify external statistics against the primary source** — when quoting an
empirical figure from a paper, blog, or external document, fetch the original
and confirm wording before inline use. User-provided snippets and HTML
previews may reframe or aggregate findings (e.g., a per-slice measure
quoted as a per-case rate). Also check experimental context (decoding
strategy, benchmark domain) — a result from a different setup may only be
directional support, not a direct rule.

**Audit the prompt's own factual claims before sending** — each claim in the verification prompt (annotation conventions, threshold values, image colour semantics) must be checked against the actual source (code, documents, data files), not session notes or handoff summaries. A verification prompt built on stale claims will pass incorrect doc state.
