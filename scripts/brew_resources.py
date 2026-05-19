"""Emit Homebrew `resource` blocks for runtime Python deps.

Walks the runtime closure starting from pyproject.toml `[project] dependencies`,
following `importlib.metadata.requires()` to gather transitives, then queries
PyPI's JSON API for each one's sdist URL + sha256. Dev-only deps and their
transitives are skipped because they're outside the closure.

Replaces homebrew-pypi-poet, which depends on the deprecated pkg_resources
and doesn't work in modern uv-managed venvs.

Run via `coily exec brew-resources`. Output pastes between the BEGIN/END
RESOURCES markers in Formula/session-lattice.rb.
"""

from __future__ import annotations

import importlib.metadata
import json
import re
import sys
import tomllib
import urllib.request
from pathlib import Path

# Skip the project root and packages that ship inside Python itself.
ROOT_SKIP = {"session-lattice"}

# `pkg ; python_version < "3.10"` and `pkg [extra]` decorations -
# strip down to bare distribution name.
NAME_RE = re.compile(r"^([A-Za-z0-9_.\-]+)")


def normalize(name: str) -> str:
    return name.lower().replace("_", "-")


def parse_dep_name(spec: str) -> str | None:
    m = NAME_RE.match(spec.strip())
    return normalize(m.group(1)) if m else None


def runtime_closure(direct: set[str]) -> set[str]:
    """BFS over importlib.metadata.requires() starting from direct deps."""
    seen: set[str] = set()
    queue = list(direct)
    while queue:
        name = queue.pop()
        if name in seen or name in ROOT_SKIP:
            continue
        seen.add(name)
        try:
            requires = importlib.metadata.requires(name) or []
        except importlib.metadata.PackageNotFoundError:
            print(f"# WARN: {name} not installed in .venv; skipping closure walk", file=sys.stderr)
            continue
        for req in requires:
            # Skip marker-gated requires that don't apply to this env.
            # `pkg ; extra == "test"` and `pkg ; sys_platform == "win32"`.
            if ";" in req:
                req_name, marker = req.split(";", 1)
                marker = marker.strip()
                # Drop extras-gated requires - they're optional install paths
                # that the formula doesn't request.
                if "extra ==" in marker or 'extra=="' in marker:
                    continue
            else:
                req_name = req
            child = parse_dep_name(req_name)
            if child and child not in seen:
                queue.append(child)
    return seen


def pypi_sdist(name: str, version: str) -> tuple[str, str]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.load(resp)
    for entry in data["urls"]:
        if entry["packagetype"] == "sdist":
            return entry["url"], entry["digests"]["sha256"]
    raise RuntimeError(f"no sdist on PyPI for {name}=={version}")


def main() -> int:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    direct = {
        parse_dep_name(dep) or ""
        for dep in pyproject["project"]["dependencies"]
    } - {""}

    closure = runtime_closure(direct)

    # Map normalized name -> (display name, version) for installed dists.
    installed: dict[str, tuple[str, str]] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        if not name:
            continue
        installed[normalize(name)] = (name, dist.version)

    for norm in sorted(closure):
        if norm not in installed:
            print(f"# WARN: {norm} in closure but not installed", file=sys.stderr)
            continue
        display, version = installed[norm]
        try:
            url, sha = pypi_sdist(display, version)
        except Exception as exc:
            print(f"# WARN: {display}=={version}: {exc}", file=sys.stderr)
            continue
        marker = " # direct" if norm in direct else ""
        print(f'  resource "{display}" do{marker}')
        print(f'    url "{url}"')
        print(f'    sha256 "{sha}"')
        print("  end")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
