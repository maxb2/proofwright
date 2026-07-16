from proofwright import load_config, run_checks
from proofwright.index import render_index, write_index
from proofwright.parse import load_wiki


def test_render_index_excludes_itself(good_config):
    wiki = load_wiki(good_config)
    out = render_index(wiki, good_config)
    assert "[[page-a]]" in out and "[[page-b]]" in out
    assert "[[index]]" not in out


def test_write_index_makes_it_current(good_copy):
    cfg = load_config(good_copy / "wiki.toml")
    # corrupt the index, then regenerate
    cfg.index_path.write_text("# Index\n\nstale\n", encoding="utf-8")
    _, report = run_checks(cfg)
    assert "stale-index" in {f.check_id for f in report.findings}

    wiki = load_wiki(cfg)
    write_index(wiki, cfg)
    _, report2 = run_checks(cfg)
    assert "stale-index" not in {f.check_id for f in report2.findings}
