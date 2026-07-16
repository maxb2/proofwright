from proofwright.parse import load_wiki


def test_page_parsing(good_config):
    wiki = load_wiki(good_config)
    page = wiki.page("page-a")
    assert page is not None
    assert page.frontmatter["title"] == "Page A"
    assert [link.target_slug for link in page.links] == ["page-b"]
    assert [c.marker for c in page.citations] == ["1"]
    # citation resolves to a source with provenance + grade
    source = page.citations[0].source
    assert source is not None
    assert source.raw_path == "raw/source-a.md"
    assert source.grade == "A"


def test_raw_inventory_and_schema(good_config):
    wiki = load_wiki(good_config)
    assert "raw/source-a.md" in wiki.raw_files
    assert "raw/source-b.md" in wiki.raw_files
    assert set(wiki.schema_slugs) == {"page-a", "page-b"}


def test_citation_lines_point_at_body(good_config):
    wiki = load_wiki(good_config)
    page = wiki.page("page-a")
    # the [1] marker sits on the first prose line of the body (file line 8)
    assert page.citations[0].line == 8
