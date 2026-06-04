# Release

Push to `main` triggers `.github/workflows/release.yml`. `mathieudutour/github-tag-action` computes semver (`default_bump: patch`, conventional commits drive minor/major), tags + cuts a GH Release, then two formula-bump jobs rewrite the url+tag+revision of both formulae via the Contents API with a skip-CI marker. `bump-tap-formula` pins them in the centralized `coilyco-flight-deck/homebrew-tap` (the primary install path, written via the forgejo Contents API with `HOMEBREW_TAP_TOKEN`); `bump-formula` keeps the in-repo `Formula/*.rb` fresh for one migration cycle as a fallback for the old direct-repo tap. Brew picks up the new tag on the next `brew upgrade`.

Never write the literal skip-CI token in a commit message body or the release workflow silently disables on that push. GitHub greps the entire message, not just the subject line. Quote it as "skip-ci marker" or "skip CI" without brackets when describing it.

## Post-push

Verify CI at +300s (the release runs on GitHub Actions; the `coily ops gh` Actions surface is playwright-only, so check the GH Release list or the Actions tab). Python virtualenv install is slower than a Go binary, so don't poll harder than that. Once the release is cut: `brew upgrade coilyco-flight-deck/tap/session-lattice coilyco-flight-deck/tap/session-lattice-puller` then `brew services restart session-lattice session-lattice-puller`. Confirm the reads service is back by hitting `localhost:7778/healthz` and checking the version field reports the just-released tag. Skip the whole loop for docs-only pushes.

## Brew-installed binary is the contract

The brew-installed binary IS the contract for staging and prod. No `uv run session-lattice serve-reads` or `serve-puller` against the staging or prod DuckDB file from a checkout, no `pip install -e .` shadowing the brew venv for staging or prod. The dev path is fine: `make watch` runs `serve-reads` and `serve-puller` in parallel from the checkout, but points at `SESSION_LATTICE_HOME=~/.session-lattice-dev` (the dev mcporter slot, port 7781), not the brew-managed `~/.session-lattice/`. The intent is "don't trample staging or prod state from a checkout", not "never run from a checkout". If a session-lattice fix is needed to unblock other work, fix-session-lattice-first: smallest fix that unblocks, commit + push, wait for the release, `brew upgrade`, return to the original repo.

## See also

- [../AGENTS.md](../AGENTS.md) - repo-local agent rules.
- [../README.md](../README.md) - human-facing intro.
- [FEATURES.md](FEATURES.md) - inventory of what ships today.
- [../.coily/coily.yaml](../.coily/coily.yaml) - allowlisted commands.

Cross-reference convention from [coilysiren/agentic-os#59](https://github.com/coilyco-flight-deck/agentic-os/issues/59).
