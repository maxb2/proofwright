"""Deterministic index / TOC regeneration.

``render_index`` is pure: same wiki in, same markdown out. The ``stale-index`` check
compares the committed index against this; ``proofwright index --write`` rewrites it.
"""

from __future__ import annotations

import os

from .config import WikiConfig
from .model import Page, Wiki
from .parse import slug_for


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


def render_index(wiki: Wiki, cfg: WikiConfig) -> str:
    """Render the canonical index markdown for ``wiki``.

    Excludes the index page itself so the file never lists itself.
    """
    index_slug = slug_for(cfg.index_path, cfg.wiki_dir) if _under_wiki(cfg) else None
    entries = [
        _entry(page, cfg)
        for page in sorted(wiki.pages, key=lambda p: p.slug)
        if page.slug != index_slug
    ]
    body = "\n".join(entries)
    return f"# Index\n\n{body}\n" if entries else "# Index\n"


def write_index(wiki: Wiki, cfg: WikiConfig) -> None:
    cfg.index_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.index_path.write_text(render_index(wiki, cfg), encoding="utf-8")


def _under_wiki(cfg: WikiConfig) -> bool:
    try:
        cfg.index_path.relative_to(cfg.wiki_dir)
        return True
    except ValueError:
        return False
