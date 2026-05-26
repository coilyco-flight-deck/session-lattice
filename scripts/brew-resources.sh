#!/usr/bin/env bash
# Print Homebrew `resource` blocks for every runtime Python dep in .venv.
# Paste between the BEGIN/END RESOURCES markers in Formula/session-lattice.rb.

set -euo pipefail

if [[ ! -d .venv ]]; then
  echo "no .venv; run 'coily exec sync' first" >&2
  exit 2
fi

.venv/bin/python scripts/brew_resources.py
