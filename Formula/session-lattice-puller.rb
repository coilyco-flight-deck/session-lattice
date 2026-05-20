class SessionLatticePuller < Formula
  desc "Puller service for session-lattice (companion formula, ships only a brew service)"
  homepage "https://github.com/coilysiren/session-lattice"
  # url/tag/revision are rewritten by the release pipeline at every tag push.
  url "ssh://git@github.com/coilysiren/session-lattice.git", tag: "v0.5.3", revision: "3684e3051b48e0530fde4667966ec1b6388e44b4"
  license "MIT"
  head "https://github.com/coilysiren/session-lattice.git", branch: "main"

  depends_on "coilysiren/session-lattice/session-lattice"

  def install
    # Companion formula. The binary ships from coilysiren/session-lattice/session-lattice;
    # this formula exists so brew can host the puller as a separately
    # restartable service. Install a marker file so brew is happy.
    (prefix/"README.md").write <<~EOS
      Companion formula for session-lattice. Ships only the puller brew
      service; the binary comes from coilysiren/session-lattice/session-lattice.
      See https://github.com/coilysiren/session-lattice/blob/main/AGENTS.md.
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
    assert_predicate prefix/"README.md", :exist?
  end
end
