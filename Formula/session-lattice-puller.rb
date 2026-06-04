class SessionLatticePuller < Formula
  desc "Puller service for session-lattice (companion formula, ships only a brew service)"
  homepage "https://forgejo.coilysiren.me/coilysiren/session-lattice"
  # url/tag/revision are rewritten by the release pipeline at every tag push.
  url "https://forgejo.coilysiren.me/coilyco-flight-deck/session-lattice.git", tag: "v0.10.4", revision: "22c15e6724c087ca5e213da93e567784ab6bfe59"
  license "MIT"
  head "https://forgejo.coilysiren.me/coilysiren/session-lattice.git", branch: "main"

  depends_on "coilysiren/session-lattice/session-lattice"

  def install
    # Marker must live in pkgshare, not keg root: brew's empty-installation
    # check skips top-level metafiles (README via Metafiles.copy?). See #17.
    (pkgshare/"README.md").write <<~EOS
      Companion formula for session-lattice. Ships only the puller brew
      service; the binary comes from coilysiren/session-lattice/session-lattice.
      See https://forgejo.coilysiren.me/coilysiren/session-lattice/src/branch/main/AGENTS.md.
    EOS
  end

  # Puller service. No port. Holds the DuckDB RW handle, pulls from repo-recall
  # on tick, materializes views. Reads service runs in the main formula.
  service do
    run [Formula["session-lattice"].opt_bin/"session-lattice", "serve-puller"]
    keep_alive true
    log_path var/"log/session-lattice-puller.log"
    error_log_path var/"log/session-lattice-puller.err.log"
    environment_variables(
      SESSION_LATTICE_HOME: "#{Dir.home}/.session-lattice",
      SESSION_LATTICE_REPO_RECALL_URL: "http://127.0.0.1:7777",
      SESSION_LATTICE_REFRESH_INTERVAL_SECONDS: "60",
      PATH: "#{HOMEBREW_PREFIX}/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
    )
  end

  test do
    assert_predicate pkgshare/"README.md", :exist?
  end
end
