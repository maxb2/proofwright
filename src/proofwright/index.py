"""Deterministic index / TOC regeneration.

``render_index`` is pure: same wiki in, same markdown out. The ``stale-index`` check
compares the committed index against this; ``proofwright index --write`` rewrites it.

The index is rendered through a Jinja2 template. The built-in default reproduces a flat
alphabetical list; a wiki may point ``[paths] index_template`` at its own template to add
prose or a folder-grouped (hierarchical) layout. Templates receive two context values:

* ``links`` — a flat, slug-sorted list of pre-rendered link lines.
* ``link_tree`` — a recursive tree of groups keyed by slug folder segments. Top-level
  (root) pages are collected under an ``Overview`` group. Each node has ``heading``,
  ``entries`` (pre-rendered link lines at that level), and ``subgroups`` (child nodes).

Link *syntax* (wikilink vs markdown) lives solely in ``_entry`` — templates only arrange
already-rendered lines, never build links themselves.
"""

from __future__ import annotations

import os

from jinja2 import Environment, StrictUndefined

from .config import WikiConfig
from .model import Page, Wiki
from .parse import slug_for

# Heading used for pages that live at the wiki root (no folder segment in their slug).
ROOT_HEADING = "Overview"

# Built-in default template: a flat, alphabetical list. Reproduces the historical output
# (``# Index\n\n<lines>\n``) so existing committed indexes stay non-stale.
DEFAULT_INDEX_TEMPLATE = """# Index

{% for link in links %}
{{ link }}
{% endfor %}"""

_ENV = Environment(
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
)


def _title(page) -> str:
    value = page.frontmatter.get("title")
    return value if isinstance(value, str) and value.strip() else page.slug


def _entry(page: Page, cfg: WikiConfig) -> str:
    """One index line, written in the wiki's configured link style."""
    title = _title(page)
    if cfg.links.style == "wikilink":
        return f"- [[{page.slug}]] — {title}"
    rel = os.path.relpath(page.path, cfg.index_path.parent).replace(os.sep, "/")
    return f"- [{title}]({rel})"


def _node(heading: str) -> dict:
    return {"heading": heading, "name": heading, "entries": [], "subgroups": []}


def _build_tree(pages: list[Page], cfg: WikiConfig) -> dict:
    """Group ``pages`` into a recursive tree keyed by slug folder segments.

    ``authors/auth-a`` nests under an ``authors`` group; ``a/b/c`` nests all the way down.
    Root-level pages (bare slug) are collected under a single ``Overview`` group so every
    link sits beneath a heading. Ordering is deterministic (slug-sorted) for stale-index.
    """
    root = _node("")
    for page in sorted(pages, key=lambda p: p.slug):
        *dirs, _leaf = page.slug.split("/")
        node = root
        for seg in dirs:
            child = next((c for c in node["subgroups"] if c["name"] == seg), None)
            if child is None:
                child = _node(seg)
                node["subgroups"].append(child)
            node = child
        node["entries"].append(_entry(page, cfg))
    _sort_subgroups(root)
    # Force root-level pages under an Overview heading, listed before the folder sections.
    if root["entries"]:
        overview = _node(ROOT_HEADING)
        overview["entries"] = root["entries"]
        root["entries"] = []
        root["subgroups"].insert(0, overview)
    return root


def _sort_subgroups(node: dict) -> None:
    node["subgroups"].sort(key=lambda c: c["name"])
    for child in node["subgroups"]:
        _sort_subgroups(child)


def _template_source(cfg: WikiConfig) -> str:
    path = cfg.index_template_path
    if path is not None:
        return path.read_text(encoding="utf-8")
    return DEFAULT_INDEX_TEMPLATE


def render_index(wiki: Wiki, cfg: WikiConfig) -> str:
    """Render the canonical index markdown for ``wiki``.

    Excludes the index page itself so the file never lists itself.
    """
    index_slug = slug_for(cfg.index_path, cfg.wiki_dir) if _under_wiki(cfg) else None
    pages = [page for page in wiki.pages if page.slug != index_slug]
    links = [_entry(page, cfg) for page in sorted(pages, key=lambda p: p.slug)]
    context = {"links": links, "link_tree": _build_tree(pages, cfg)}
    template = _ENV.from_string(_template_source(cfg))
    return template.render(**context)


def write_index(wiki: Wiki, cfg: WikiConfig) -> None:
    cfg.index_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.index_path.write_text(render_index(wiki, cfg), encoding="utf-8")


def _under_wiki(cfg: WikiConfig) -> bool:
    try:
        cfg.index_path.relative_to(cfg.wiki_dir)
        return True
    except ValueError:
        return False
