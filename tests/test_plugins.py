import shutil
import textwrap

from proofwright import load_config, run_checks

from conftest import FIXTURES, GOOD

MD = FIXTURES / "mini-wiki-md"
PROVENANCE_PLUGIN = FIXTURES / "pw_provenance_plugin.py"

PLUGIN_SRC = textwrap.dedent(
    """
    from proofwright.report import Finding

    def a_custom_check(wiki, cfg):
        for page in wiki.pages:
            yield Finding(
                check_id="custom-note",
                severity="info",
                message="seen by custom plugin",
                path=str(page.path),
                line=1,
            )

    def register(registry):
        registry.add("custom-note", "info", a_custom_check)
    """
)


def test_config_module_plugin_runs(tmp_path, monkeypatch):
    (tmp_path / "pw_custom_plugin.py").write_text(PLUGIN_SRC, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))

    cfg = load_config(GOOD / "wiki.toml")
    cfg.plugins.modules = ["pw_custom_plugin"]
    cfg.plugins.load_entry_points = False

    _, report = run_checks(cfg)
    ids = {f.check_id for f in report.findings}
    assert "custom-note" in ids
    # good wiki still clean of real findings; plugin only adds info
    assert report.counts()["error"] == 0


def test_frontmatter_sources_plugin(tmp_path):
    """The wiki-local provenance plugin flags a book with no sources, via cfg.extra."""
    dest = tmp_path / "w"
    shutil.copytree(MD, dest)
    shutil.copy(PROVENANCE_PLUGIN, dest / "pw_provenance_plugin.py")
    (dest / "wiki.toml").write_text(
        textwrap.dedent(
            """
            [paths]
            raw = "raw/"
            wiki = "wiki/"
            schema = "CLAUDE.md"
            index = "wiki/index.md"
            [links]
            style = "markdown"
            [citation]
            claim_policy = "off"
            [plugins]
            modules = ["pw_provenance_plugin"]
            [frontmatter_sources]
            field = "sources"
            require_for = ["book"]
            """
        ),
        encoding="utf-8",
    )
    _, report = run_checks(load_config(dest / "wiki.toml"))
    ids_by_page = {(f.check_id, f.path) for f in report.findings}
    # book-b has type book but no sources -> flagged; book-a has valid sources -> not
    assert ("sources-missing", "wiki/library/book-b.md") in ids_by_page
    assert not any(cid == "sources-missing" and "book-a" in p for cid, p in ids_by_page)
