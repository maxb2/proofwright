import sys
import textwrap

from proofwright import load_config, run_checks

from conftest import GOOD

PLUGIN_SRC = textwrap.dedent(
    '''
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
    '''
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
