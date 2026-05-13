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

## Analysis Document Sections

**Section content must match section name** — a section whose heading names
a specific scope (e.g. "Dataset Gaps", "Open Bugs") should contain only items
matching that scope. Scope exclusions ("X is out of scope") belong in preamble
or methodology notes. When auditing, ask: "Is this missing something that
should be there, or explaining why something isn't there?" Only the former
belongs.

**Drop zero-finding sections** — a section that reports only a negative
result (zero failures, zero errors) with no decision, no risk, and no
verifiable before/after for the reader adds length without insight. Remove
rather than retain for completeness.

**Use specific descriptive status labels in risk/limitation sections** — name
the actual state or proposed action ("instability measured", "coverage metric
proposed") rather than generic abstract labels ("proposed, not implemented").
Specific labels communicate actionability without forcing the reader to parse
prose. Use blockquote format (`>`) to visually distinguish status notes. When
no mitigation exists, prefix with "Follow-up —" or "Known limitation —"
instead of forcing "Mitigation status —".

**Unify terminology when sections propose the same idea** — if two sections
propose the same metric family or mechanism under different names, pick one
term and cross-reference from the second section ("this is the same approach
proposed in §X"). Distinguish directional framing precisely (e.g.,
summary-to-source vs source-to-summary) rather than reusing a loose term
across both.

**Label terminology must match data behaviour** — a label like "flips" implies
a binary pass/fail switch and should be reserved for cases where at least one
run fails and at least one passes. Use "unstable" when the score varies but
never crosses the threshold. Do not use a binary-verdict label for a
non-binary phenomenon.

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

**Cross-references must directly support the current claim** — only include
`see also §X` when the linked section qualifies or supports the specific
point. Tangential links — where the referenced section is related but does
not speak to the current claim — add noise without information. Remove them.

**Do not use "Same" shorthand in tables** — a cell that says "Same" or
"Same — \<qualifier\>" relies on adjacent rows staying put. If rows shift,
the reference silently breaks. Repeat the explicit note text instead.

**Research paper links use author-year format** — `[Author et al., Year](url)`. Do not use bare URLs or generic link text ("literature", "here", "the paper"). Not yet lint-enforced; check manually when adding citations.

## External-Reader Documents

**Frame before presenting** — introductory sections carry more weight than they
appear to. Do not assume the reader has codebase context; make the analytical
frame explicit before findings appear.

**Gloss technical shorthand** — terms like "NLI", "temperature=0", or "statement decomposition" will lose readers without ML background. Prefer a plain-language mechanism explanation alongside or instead of the shorthand.

## Language

Use **British English** throughout documentation (`colour`, `behaviour`,
`summarise`, `colourmap`). Exception: do not change doc prose spelling for a
term whose code identifier still uses a different spelling — that creates a
mismatch between docs and code. Update prose only after the rename lands in
the codebase.
