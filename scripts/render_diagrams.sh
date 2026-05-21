#!/usr/bin/env bash
set -euo pipefail

render_diagram() {
  local name="$1"

  npx @mermaid-js/mermaid-cli \
    -i "docs/diagrams/${name}.mmd" \
    -o "docs/images/${name}.svg" \
    -c docs/diagrams/mermaid-config.json
}

render_diagram architecture
render_diagram injection-robustness
