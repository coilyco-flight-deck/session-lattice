class SessionLattice < Formula
  include Language::Python::Virtualenv

  desc "Materialized-view service over Claude session data (embedded DuckDB)"
  homepage "https://github.com/coilysiren/session-lattice"
  # url/tag/revision are rewritten by the release pipeline at every tag push.
  url "ssh://git@github.com/coilysiren/session-lattice.git", tag: "v0.6.1", revision: "9c2c7e1f0484d80f06fdec4e066b058995a55064"
  license "MIT"
  head "https://github.com/coilysiren/session-lattice.git", branch: "main"

  depends_on "duckdb"
  depends_on "python@3.13"
  depends_on "rust" => :build

  # Runtime Python resource blocks. Regenerate after a dep change with:
  #   coily exec sync && coily exec brew-resources
  # then paste the output between the BEGIN/END markers below.
  #
  # BEGIN RESOURCES (managed by coily exec brew-resources)
  resource "annotated-doc" do
    url "https://files.pythonhosted.org/packages/57/ba/046ceea27344560984e26a590f90bc7f4a75b06701f653222458922b558c/annotated_doc-0.0.4.tar.gz"
    sha256 "fbcda96e87e9c92ad167c2e53839e57503ecfda18804ea28102353485033faa4"
  end

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz"
    sha256 "aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89"
  end

  resource "anyio" do
    url "https://files.pythonhosted.org/packages/19/14/2c5dd9f512b66549ae92767a9c7b330ae88e1932ca57876909410251fe13/anyio-4.13.0.tar.gz"
    sha256 "334b70e641fd2221c1505b3890c69882fe4a2df910cba14d97019b90b24439dc"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/25/ee/6caf7a40c36a1220410afe15a1cc64993a1f864871f698c0f93acb72842a/certifi-2026.4.22.tar.gz"
    sha256 "8d455352a37b71bf76a79caa83a3d6c25afee4a385d632127b6afb3963f1c580"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/23/e4/796662cd90cf80e3a363c99db2b88e0e394b988a575f60a17e16440cd011/click-8.4.0.tar.gz"
    sha256 "638f1338fe1235c8f4e008e4a8a254fb5c5fbdcbb40ece3c9142ebb78e792973"
  end

  resource "duckdb" do
    url "https://files.pythonhosted.org/packages/0c/66/744b4931b799a42f8cb9bc7a6f169e7b8e51195b62b246db407fd90bf15f/duckdb-1.5.2.tar.gz"
    sha256 "638da0d5102b6cb6f7d47f83d0600708ac1d3cb46c5e9aaabc845f9ba4d69246"
  end

  resource "fastapi" do
    url "https://files.pythonhosted.org/packages/5d/45/c130091c2dfa061bbfe3150f2a5091ef1adf149f2a8d2ae769ecaf6e99a2/fastapi-0.136.1.tar.gz"
    sha256 "7af665ad7acfa0a3baf8983d393b6b471b9da10ede59c60045f49fbc89a0fa7f"
  end

  resource "h11" do
    url "https://files.pythonhosted.org/packages/01/ee/02a2c011bdab74c6fb3c75474d40b3052059d95df7e73351460c8588d963/h11-0.16.0.tar.gz"
    sha256 "4e35b956cf45792e4caa5885e69fba00bdbc6ffafbfa020300e549b208ee5ff1"
  end

  resource "httpcore" do
    url "https://files.pythonhosted.org/packages/06/94/82699a10bca87a5556c9c59b5963f2d039dbd239f25bc2a63907a05a14cb/httpcore-1.0.9.tar.gz"
    sha256 "6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8"
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/b1/df/48c586a5fe32a0f01324ee087459e112ebb7224f646c0b5023f5e79e9956/httpx-0.28.1.tar.gz"
    sha256 "75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/82/77/7b3966d0b9d1d31a36ddf1746926a11dface89a83409bf1483f0237aa758/idna-3.15.tar.gz"
    sha256 "ca962446ea538f7092a95e057da437618e886f4d349216d2b1e294abfdb65fdc"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/18/a5/b60d21ac674192f8ab0ba4e9fd860690f9b4a6e51ca5df118733b487d8d6/pydantic-2.13.4.tar.gz"
    sha256 "c40756b57adaa8b1efeeced5c196f3f3b7c435f90e84ea7f443901bec8099ef6"
  end

  resource "pydantic_core" do
    url "https://files.pythonhosted.org/packages/9d/56/921726b776ace8d8f5db44c4ef961006580d91dc52b803c489fafd1aa249/pydantic_core-2.46.4.tar.gz"
    sha256 "62f875393d7f270851f20523dd2e29f082bcc82292d66db2b64ea71f64b6e1c1"
  end

  resource "starlette" do
    url "https://files.pythonhosted.org/packages/81/69/17425771797c36cded50b7fe44e850315d039f28b15901ab44839e70b593/starlette-1.0.0.tar.gz"
    sha256 "6a4beaf1f81bb472fd19ea9b918b50dc3a77a6f2e190a12954b25e6ed5eea149"
  end

  resource "typing_extensions" do
    url "https://files.pythonhosted.org/packages/72/94/1a15dd82efb362ac84269196e94cf00f187f7ed21c242792a923cdb1c61f/typing_extensions-4.15.0.tar.gz"
    sha256 "0cea48d173cc12fa28ecabc3b837ea3cf6f38c6d1136f85cbaaf598984861466"
  end

  resource "typing-inspection" do
    url "https://files.pythonhosted.org/packages/55/e3/70399cb7dd41c10ac53367ae42139cf4b1ca5f36bb3dc6c9d33acdb43655/typing_inspection-0.4.2.tar.gz"
    sha256 "ba561c48a67c5958007083d386c3295464928b01faa735ab8547c5692e87f464"
  end

  resource "uvicorn" do
    url "https://files.pythonhosted.org/packages/f6/b1/8e7077a8641086aea449e1b5752a570f1b5906c64e0a33cd6d93b63a066b/uvicorn-0.47.0.tar.gz"
    sha256 "7c9a0ea1a9414106bbab7324609c162d8fa0cdcdcb703060987269d77c7bb533"
  end
  # END RESOURCES

  def install
    virtualenv_install_with_resources
  end

  # Reads service binds the session-lattice-staging mcporter slot on 127.0.0.1:7778.
  # Prod runs on kai-server via the same formula; dev runs from checkout
  # via `make watch` on a different port. The puller is a separate brew
  # service shipped by the session-lattice-puller companion formula so
  # reads and puller can be restarted independently. See /AGENTS.md.
  service do
    run [opt_bin/"session-lattice", "serve-reads"]
    keep_alive true
    log_path var/"log/session-lattice-reads.log"
    error_log_path var/"log/session-lattice-reads.err.log"
    environment_variables(
      SESSION_LATTICE_HOME: "#{Dir.home}/.session-lattice",
      SESSION_LATTICE_HOST: "127.0.0.1",
      SESSION_LATTICE_PORT: "7778",
      PATH: "#{HOMEBREW_PREFIX}/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
    )
  end

  def caveats
    <<~EOS
      session-lattice ships two brew services. Start both:
        brew services start coilysiren/session-lattice/session-lattice
        brew services start coilysiren/session-lattice/session-lattice-puller

      To configure either service (port, repo-recall URL, refresh interval, etc.):
        brew services edit session-lattice
        brew services edit session-lattice-puller
        brew services restart <name>
      Edits to the service files persist across `brew upgrade`.

      The DuckDB database file lives at ~/.session-lattice/session-lattice.duckdb.
      Attach the DuckDB UI read-only against the live file:
        duckdb -readonly ~/.session-lattice/session-lattice.duckdb -ui
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/session-lattice --version")
    assert_match "session-lattice", shell_output("#{bin}/session-lattice --help")
  end
end
