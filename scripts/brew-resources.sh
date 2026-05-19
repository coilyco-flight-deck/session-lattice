#!/usr/bin/env bash
# Print Homebrew `resource` blocks for every Python dependency in the
# synced uv venv. Pipe into Formula/session-lattice.rb between the
# managed BEGIN/END RESOURCES markers.
#
#   coily exec brew-resources > /tmp/resources
#   # then hand-merge between the markers in Formula/session-lattice.rb
#
# Runs `homebrew-pypi-poet` against the venv that `uv sync` produced.
# Poet emits one `resource "<name>" do ... end` block per top-level + transitive
# distribution, ready to paste into the formula.

set -euo pipefail

if [[ ! -d .venv ]]; then
  echo "no .venv; run 'coily exec sync' first" >&2
  exit 2
fi

if ! .venv/bin/python -c "import poet" >/dev/null 2>&1; then
  .venv/bin/pip install --quiet homebrew-pypi-poet
fi

# session-lattice itself is the installed root package - exclude it.
.venv/bin/poet -f session-lattice 2>/dev/null | sed '/^class /,$d'
