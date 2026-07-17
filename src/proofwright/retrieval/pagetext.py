"""The canonical text of a page for retrieval.

One definition of "what text represents a page" — the frontmatter ``title`` plus the body —
shared by every candidate stream (BM25, vector) so they index the same content.
"""

from __future__ import annotations

from ..model import Page


def page_text(page: Page) -> str:
    """Return the retrieval text for ``page``: its title line then its body."""
    title = page.frontmatter.get("title")
    title = title if isinstance(title, str) else ""
    return f"{title}\n{page.body}"
