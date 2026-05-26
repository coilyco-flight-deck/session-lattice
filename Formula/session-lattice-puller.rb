class SessionLatticePuller < Formula
  desc "Puller service for session-lattice (companion formula, ships only a brew service)"
  homepage "https://forgejo.coilysiren.me/coilysiren/session-lattice"
  # url/tag/revision are rewritten by the release pipeline at every tag push.
  url "https://forgejo.coilysiren.me/coilysiren/session-lattice.git", tag: "v0.8.3", revision: "26bb0864e616d7d8d49ed3a3f0d283ec0b75c92b"
  license "MIT"
  head "https://forgejo.coilysiren.me/coilysiren/session-lattice.git", branch: "main"

  depends_on "coilysiren/session-lattice/session-lattice"

  def install
    # Companion formula. Binary ships from session-lattice; this hosts the
    # puller as a separately restartable brew service. Marker file keeps brew happy.
    (prefix/"README.md").write <<~EOS
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
    assert_predicate prefix/"README.md", :exist?
  end
end
