# Personal Standards

Reusable conventions for AI assistants working on my projects.

## Structure

```text
personal-standards/
├── general/
│   ├── style-guide.md  # Clarity, naming conventions
│   └── testing.md      # Test naming, structure, organization
├── python/
│   ├── style-guide.md  # Python-specific code conventions
│   └── testing.md      # Pytest patterns
├── ai-workflow.md      # Language-agnostic workflow rules
├── documentation.md    # Documentation standards
└── README.md
```

## Usage

### As a Git Subtree

```bash
# Add to a project
git subtree add --prefix .standards https://github.com/gsiam/personal-standards.git main --squash


# Add a remote for easier commands
git remote add standards https://github.com/gsiam/personal-standards.git


# Add a remote for easier commands
git remote add standards git@github.com:USERNAME/personal-standards.git

# Pull updates
git subtree pull --prefix=.standards standards main --squash

# Push changes back to standards repo
git subtree push --prefix=.standards standards main
```

### Reference in CLAUDE.md

Reference by directory so new standard files are picked up automatically.
Exclude directories for languages not used in the project.

```markdown
## Standards

Refer to `.standards/general/`, `.standards/<language>/`, and
`.standards/ai-workflow.md` for general conventions.
```
