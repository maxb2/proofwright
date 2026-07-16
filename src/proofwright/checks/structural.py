"""Structural checks: orphans, missing pages, broken links, stale index, provenance."""

from __future__ import annotations

from ..config import WikiConfig
from ..graph import build_graph
from ..index import render_index
from ..model import Wiki
from ..report import Finding
from . import registry, rel as _rel


@registry.register("broken-link", severity="error")
def broken_links(wiki: Wiki, cfg: WikiConfig):
    for page in wiki.pages:
        for link in page.links:
            if not wiki.has_page(link.target_slug):
                yield Finding(
                    check_id="broken-link",
                    severity="error",
                    message=f"wikilink to missing page [[{link.target_slug}]]",
                    path=_rel(wiki, page.path),
                    line=link.line,
                    data={"target": link.target_slug},
                )


@registry.register("orphan-page", severity="warn")
def orphan_pages(wiki: Wiki, cfg: WikiConfig):
    inbound = wiki.inbound_counts()
    roots = set(cfg.graph.roots)
    for page in wiki.pages:
        if page.slug in roots:
            continue
        if inbound.get(page.slug, 0) == 0:
            yield Finding(
                check_id="orphan-page",
                severity="warn",
                message="page has no inbound wikilinks (orphan)",
                path=_rel(wiki, page.path),
                line=1,
                data={"slug": page.slug},
            )


@registry.register("missing-page", severity="error")
def missing_pages(wiki: Wiki, cfg: WikiConfig):
    """A slug declared in the schema has no page file."""
    for slug in wiki.schema_slugs:
        if not wiki.has_page(slug):
            yield Finding(
                check_id="missing-page",
                severity="error",
                message=f"schema declares [[{slug}]] but no page file exists",
                path=_rel(wiki, cfg.schema_path),
                line=1,
                data={"slug": slug},
            )


@registry.register("stale-index", severity="error")
def stale_index(wiki: Wiki, cfg: WikiConfig):
    index_path = cfg.index_path
    expected = render_index(wiki, cfg)
    actual = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    if actual.strip() != expected.strip():
        yield Finding(
            check_id="stale-index",
            severity="error",
            message="index is out of date; run `proofwright index --write`",
            path=_rel(wiki, index_path),
            line=1,
        )


@registry.register("missing-provenance", severity="error")
def missing_provenance(wiki: Wiki, cfg: WikiConfig):
    """A referenced source names no raw/ file, or names one that does not exist."""
    for page in wiki.pages:
        for marker, source in page.sources.items():
            if source.raw_path is None:
                yield Finding(
                    check_id="missing-provenance",
                    severity="error",
                    message=f"reference [{marker}] names no source file in raw/",
                    path=_rel(wiki, page.path),
                    line=1,
                    data={"marker": marker},
                )
            elif source.raw_path not in wiki.raw_files:
                yield Finding(
                    check_id="missing-provenance",
                    severity="error",
                    message=f"reference [{marker}] points to missing raw file "
                    f"'{source.raw_path}'",
                    path=_rel(wiki, page.path),
                    line=1,
                    data={"marker": marker, "raw_path": source.raw_path},
                )
