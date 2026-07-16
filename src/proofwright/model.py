"""Content-agnostic data model for a wiki.

Nothing here knows the subject matter. A :class:`Wiki` is a bag of parsed pages plus the
``raw/`` inventory and the resolved reference table.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class WikiLink:
    """An explicit ``[[target]]`` or ``[[target|label]]`` reference."""

    target_slug: str
    line: int
    raw: str
    label: str | None = None


@dataclass
class Citation:
    """A ``[n]`` citation marker in page body text."""

    marker: str  # the numeric key, e.g. "3"
    line: int
    source: "Source | None" = None  # resolved during Wiki.load


@dataclass
class Source:
    """A reference entry: ``[n]. <text>`` mapping a marker to provenance."""

    id: str  # the numeric key, e.g. "3"
    text: str  # the raw reference line text
    raw_path: str | None = None  # a path under raw/, if the entry names one
    url: str | None = None
    grade: str | None = None


@dataclass
class Page:
    path: Path
    slug: str
    frontmatter: dict = field(default_factory=dict)
    body: str = ""
    lines: list[str] = field(default_factory=list)
    body_start: int = 1  # 1-based file line where the body (post-frontmatter) begins
    links: list[WikiLink] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    sources: dict[str, Source] = field(default_factory=dict)  # marker -> Source
    ref_lines: set[int] = field(default_factory=set)  # file lines of the references block
    fm_error: str | None = None  # YAML parse error, if the frontmatter block is invalid

    @property
    def body_chars(self) -> int:
        return len(self.body.strip())


@dataclass
class Wiki:
    root: Path
    pages: list[Page] = field(default_factory=list)
    raw_files: set[str] = field(default_factory=set)  # paths relative to wiki root
    schema_slugs: list[str] = field(default_factory=list)  # page types declared in schema

    _by_slug: dict[str, Page] = field(default_factory=dict, repr=False)

    def index_pages(self) -> None:
        self._by_slug = {p.slug: p for p in self.pages}

    def page(self, slug: str) -> Page | None:
        return self._by_slug.get(slug)

    def has_page(self, slug: str) -> bool:
        return slug in self._by_slug

    def inbound_counts(self) -> dict[str, int]:
        """Count inbound wikilinks per slug (targets, whether or not they exist)."""
        counts: dict[str, int] = {}
        for page in self.pages:
            for link in page.links:
                counts[link.target_slug] = counts.get(link.target_slug, 0) + 1
        return counts
