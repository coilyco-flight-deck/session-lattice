#!/usr/bin/env bash
# Print Homebrew `resource` blocks for every runtime Python dependency in
# the synced .venv. Pipe between the BEGIN/END RESOURCES markers in
# Formula/session-lattice.rb.
#
#   coily exec brew-resources > /tmp/resources
#   # hand-merge between the markers in Formula/session-lattice.rb
#
# Walks installed distributions via importlib.metadata, queries PyPI's
# JSON API for sdist URL + sha256. No external Python deps - replaces
# homebrew-pypi-poet, which depends on the deprecated pkg_resources.

set -euo pipefail

if [[ ! -d .venv ]]; then
  echo "no .venv; run 'coily exec sync' first" >&2
  exit 2
fi

.venv/bin/python scripts/brew_resources.py
