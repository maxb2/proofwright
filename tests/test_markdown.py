from proofwright import load_config, run_checks
from proofwright.parse import load_wiki, resolve_md_target

from conftest import FIXTURES

MD = FIXTURES / "mini-wiki-md"


def md_config():
    return load_config(MD / "wiki.toml")


def test_resolve_md_target():
    page_dir = MD / "wiki" / "library"
    wiki_dir = MD / "wiki"
    # internal page link -> slug relative to wiki dir
    assert resolve_md_target("../authors/auth-a.md", page_dir, wiki_dir) == "authors/auth-a"
    assert resolve_md_target("book-a.md", page_dir, wiki_dir) == "library/book-a"
    # anchors are stripped
    assert resolve_md_target("book-a.md#summary", page_dir, wiki_dir) == "library/book-a"
    # external + out-of-wiki resolve to None (not graph edges)
    assert resolve_md_target("https://example.com", page_dir, wiki_dir) is None
    assert resolve_md_target("../../raw/manual/books.md", page_dir, wiki_dir) is None


def test_markdown_links_build_graph():
    wiki = load_wiki(md_config())
    book_a = wiki.page("library/book-a")
    assert [l.target_slug for l in book_a.links] == ["authors/auth-a"]


def test_markdown_broken_link_detected():
    _, report = run_checks(md_config())
    errors = {f.check_id for f in report.findings if f.severity == "error"}
    assert errors == {"broken-link"}
    bl = next(f for f in report.findings if f.check_id == "broken-link")
    assert bl.path == "wiki/library/book-b.md"
    assert bl.data["target"] == "library/ghost"
