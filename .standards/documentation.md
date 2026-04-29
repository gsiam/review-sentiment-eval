# Documentation Standards

## Keeping Docs in Sync

- **Check README.md, CLAUDE.md, and `docs/design-decisions.md` after any user-facing change** — new CLI options, renamed files, changed dependencies, or altered architecture should be reflected in the appropriate file. Don't wait for a separate "docs" step.

## Flowcharts (Mermaid)

- **Phrase decision nodes so "Yes" is the positive outcome** - Readers expect "Yes" to mean success. Use "Valid?" (Yes → continue) not "Invalid?" (No → continue)
- **Use subgraphs** for visual grouping of related operations
- **Show parallel data flows** with branching arrows when a node feeds multiple paths
- **Use collector nodes** to merge multiple arrows into one (e.g., `A & B & C --> OUT`)

## Analysis Document Prose

**Cite statistics precisely** — write "lowest median" not "lowest score" when a
table has per-run ranges. A reader cannot tell whether "score" means a single
run value or the median across runs.

**Let table markers do their job** — if a table already encodes information with
a marker (e.g., `*` for instability), prose should add interpretation, not repeat
the encoding. Write what the marker *means* for this case; don't restate that it
is "flagged unstable."

**Use a key when a symbol has multiple meanings** — if a verdict marker encodes
two structurally distinct outcomes (e.g., universal miss vs run-level instability),
the preamble must include a key that distinguishes them. Relying on context to
disambiguate produces tables that appear consistent but are not.

## Cross-References and Links

**Link on first mention, plain text after** — when the same section or document
is referenced more than once in close proximity (same paragraph or adjacent
sentences), hyperlink only the first occurrence. Repeat links add visual noise
without helping the reader navigate.

**Check links after renaming a heading** — renaming a heading silently breaks
every anchor that points to it. Before committing, grep `docs/` for the old
anchor slug and update all occurrences. Then run the link checker to confirm:

```bash
lychee --include-fragments --root-dir . README.md CLAUDE.md 'docs/**/*.md'
```

## External-Reader Documents

**Frame before presenting** — introductory sections carry more weight than they
appear to. Do not assume the reader has codebase context; make the analytical
frame explicit before findings appear.

## Language

Use **British English** throughout documentation (`colour`, `behaviour`,
`summarise`, `colourmap`). Exception: do not change doc prose spelling for a
term whose code identifier still uses a different spelling — that creates a
mismatch between docs and code. Update prose only after the rename lands in
the codebase.
