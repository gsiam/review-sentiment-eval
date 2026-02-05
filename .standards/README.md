# Personal Standards

Reusable conventions for AI assistants working on my projects.

## Structure

```text
personal-standards/
├── python/
│   ├── style-guide.md    # Code conventions
│   └── testing.md        # Testing patterns
├── ai-workflow.md        # Language-agnostic workflow rules
└── README.md
```

## Usage

### As a Git Subtree

```bash
# Add to a project
git subtree add --prefix .standards git@github.com:USERNAME/personal-standards.git main --squash

# Add a remote for easier commands
git remote add standards git@github.com:USERNAME/personal-standards.git

# Pull updates
git subtree pull --prefix=.standards standards main --squash

# Push changes back to standards repo
git subtree push --prefix=.standards standards main
```

### Reference in CLAUDE.md

```markdown
## Standards

Follow the conventions in:
- [Python Style Guide](.standards/python/style-guide.md)
- [Python Testing](.standards/python/testing.md)
- [AI Workflow Rules](.standards/ai-workflow.md)
```
