from pathlib import Path

from proofwright import load_config, run_checks
from proofwright.index import _build_tree, render_index, write_index
from proofwright.model import Page
from proofwright.parse import load_wiki

MD_WIKI = Path(__file__).parent / "fixtures" / "mini-wiki-md"


def _page(slug: str) -> Page:
    return Page(path=Path(f"wiki/{slug}.md"), slug=slug, frontmatter={"title": slug})


def test_build_tree_groups_by_folder_and_forces_overview(good_config):
    pages = [_page("home"), _page("about"), _page("guides/setup"), _page("guides/adv/tuning")]
    tree = _build_tree(pages, good_config)
    headings = [g["heading"] for g in tree["subgroups"]]
    # Root pages collected under Overview, which sorts before folder sections.
    assert headings == ["Overview", "guides"]
    overview = tree["subgroups"][0]
    assert overview["entries"] and all("[[home]]" in e or "[[about]]" in e for e in overview["entries"])
    # Recursive nesting: guides/adv/tuning sits under guides -> adv.
    guides = tree["subgroups"][1]
    assert [s["heading"] for s in guides["subgroups"]] == ["adv"]
    assert "[[guides/adv/tuning]]" in guides["subgroups"][0]["entries"][0]


def test_custom_template_renders_headings(tmp_path):
    import shutil

    dest = tmp_path / "wiki"
    shutil.copytree(MD_WIKI, dest)
    shutil.copy(
        Path(__file__).parent.parent / "templates" / "index-hierarchical.md",
        dest / "index-hierarchical.md",
    )
    cfg = load_config(dest / "wiki.toml")
    cfg.paths.index_template = "index-hierarchical.md"
    out = render_index(load_wiki(cfg), cfg)
    assert "## authors" in out and "## library" in out
    assert "[Book A](library/book-a.md)" in out


def test_default_output_unchanged_for_md_wiki():
    cfg = load_config(MD_WIKI / "wiki.toml")
    out = render_index(load_wiki(cfg), cfg)
    committed = (MD_WIKI / "wiki" / "index.md").read_text(encoding="utf-8")
    assert out.strip() == committed.strip()


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
