# Documentation Standards

## Keeping Docs in Sync

- **Check README.md and CLAUDE.md after any user-facing change** — new CLI options, renamed files, changed dependencies, or altered architecture should be reflected in both. Don't wait for a separate "docs" step.

## Flowcharts (Mermaid)

- **Phrase decision nodes so "Yes" is the positive outcome** - Readers expect "Yes" to mean success. Use "Valid?" (Yes → continue) not "Invalid?" (No → continue)
- **Use subgraphs** for visual grouping of related operations
- **Show parallel data flows** with branching arrows when a node feeds multiple paths
- **Use collector nodes** to merge multiple arrows into one (e.g., `A & B & C --> OUT`)
