"""Per-wiki configuration.

All per-wiki variance lives here — paths, vocabularies, thresholds, policies. No
subject-matter knowledge lives in any check; a check reads it from ``WikiConfig``. Loaded
from a declarative ``wiki.toml`` into a typed dataclass, with sensible defaults so a wiki
works with a near-empty file.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PathsConfig:
    raw: str = "raw/"
    wiki: str = "wiki/"
    schema: str = "CLAUDE.md"
    index: str = "wiki/index.md"
    # Optional Jinja2 template for the generated index, relative to the wiki root.
    # None = built-in flat list. Templates receive ``links`` and ``link_tree``.
    index_template: str | None = None


@dataclass
class FrontmatterConfig:
    required: list[str] = field(default_factory=lambda: ["title"])
    # key -> type name in {"str", "int", "float", "bool", "list", "date"}
    types: dict[str, str] = field(default_factory=dict)
    # Allowed tag vocabulary; empty list means "any tag allowed".
    tags: list[str] = field(default_factory=list)
    # Frontmatter key holding a page's list of tags.
    tags_field: str = "tags"
    # Frontmatter key holding the grade a page relies on (for surfaced-grade check).
    grade_field: str = "grade"


@dataclass
class GradesConfig:
    # Fixed reliability vocabulary. Empty means grading is not enforced.
    vocab: list[str] = field(default_factory=list)


@dataclass
class LinksConfig:
    # How cross-references are written:
    #   "wikilink" = [[slug]] (Obsidian style)
    #   "markdown" = [label](relative/path.md)
    #   "both"     = accept either
    style: str = "wikilink"


@dataclass
class CitationConfig:
    # How ``[n]`` markers map to sources: "section" = a References section of
    # ``[n]. <text mentioning a raw/ path or url>`` lines.
    references: str = "section"
    # Heading text (case-insensitive) that starts the references section.
    references_heading: str = "References"
    # What counts as a claim line needing citation coverage:
    #   "paragraph" = every prose paragraph, "off" = disable coverage flagging.
    claim_policy: str = "paragraph"


@dataclass
class FreshnessConfig:
    recency_field: str = "updated"
    stale_after_days: int = 180


@dataclass
class GraphConfig:
    # Pages allowed to have no inbound links (entry points), by slug.
    roots: list[str] = field(default_factory=lambda: ["index"])
    # A page with >= this many inbound links is a "hub".
    hub_min_inbound: int = 5
    # A hub whose body is shorter than this (chars) is a "hub stub".
    stub_max_chars: int = 200


@dataclass
class VectorConfig:
    # Dense embedding stream, off by default. Requires the ``vector`` extra
    # (``pip install proofwright[vector]``); configured under ``[retrieval.vector]``.
    enabled: bool = False
    # Embedding backend. Room to grow: "onnx", "sentence-transformers".
    backend: str = "model2vec"
    # Model id (HuggingFace) or local directory for the chosen backend.
    model: str = "minishlab/potion-retrieval-32M"
    # Per-stream candidate cap before fusion.
    candidate_limit: int = 50


@dataclass
class RetrievalConfig:
    # BM25-Okapi term-frequency saturation and length-normalization.
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    # Reciprocal rank fusion damping constant.
    rrf_k: int = 60
    # Graph-expansion reach and per-hop score decay.
    graph_hops: int = 2
    graph_decay: float = 0.5
    # Number of top BM25 hits used to seed graph expansion.
    seed_count: int = 10
    # Per-stream candidate cap before fusion.
    candidate_limit: int = 50
    # Final number of results returned.
    top_n: int = 10
    # Minimum token length kept during tokenization.
    min_token_len: int = 2
    # Optional dense vector stream, configured under ``[retrieval.vector]``.
    vector: VectorConfig = field(default_factory=VectorConfig)


@dataclass
class ChecksConfig:
    # Severities that cause a nonzero exit code.
    fail_on: list[str] = field(default_factory=lambda: ["error"])
    # Check ids to skip.
    disabled: list[str] = field(default_factory=list)


@dataclass
class PluginsConfig:
    # Dotted module paths, each exposing ``register(registry)``.
    modules: list[str] = field(default_factory=list)
    # Whether to also load checks from the ``proofwright.checks`` entry-point group.
    load_entry_points: bool = True


@dataclass
class WikiConfig:
    root: Path
    paths: PathsConfig = field(default_factory=PathsConfig)
    frontmatter: FrontmatterConfig = field(default_factory=FrontmatterConfig)
    grades: GradesConfig = field(default_factory=GradesConfig)
    links: LinksConfig = field(default_factory=LinksConfig)
    citation: CitationConfig = field(default_factory=CitationConfig)
    freshness: FreshnessConfig = field(default_factory=FreshnessConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    checks: ChecksConfig = field(default_factory=ChecksConfig)
    plugins: PluginsConfig = field(default_factory=PluginsConfig)
    # The full parsed TOML, so plugins can read their own config tables
    # (e.g. cfg.extra["frontmatter_sources"]). Core never reads this.
    extra: dict = field(default_factory=dict)

    # --- resolved absolute paths -------------------------------------------------
    @property
    def raw_dir(self) -> Path:
        return self.root / self.paths.raw

    @property
    def wiki_dir(self) -> Path:
        return self.root / self.paths.wiki

    @property
    def schema_path(self) -> Path:
        return self.root / self.paths.schema

    @property
    def index_path(self) -> Path:
        return self.root / self.paths.index

    @property
    def index_template_path(self) -> Path | None:
        """Resolved path to a custom index template, or None for the built-in default."""
        if not self.paths.index_template:
            return None
        return self.root / self.paths.index_template

    def index_slug(self) -> str | None:
        """Slug of the generated index page, or None if the index lives outside wiki/."""
        try:
            rel = self.index_path.relative_to(self.wiki_dir).with_suffix("")
            return rel.as_posix()
        except ValueError:
            return None


def _build(section_cls, data: dict | None):
    """Instantiate a config dataclass from a dict, ignoring unknown keys."""
    data = data or {}
    known = {f.name for f in section_cls.__dataclass_fields__.values()}
    return section_cls(**{k: v for k, v in data.items() if k in known})


def load_config(path: str | Path) -> WikiConfig:
    """Load ``wiki.toml`` into a :class:`WikiConfig`.

    ``path`` points at the TOML file; the wiki root is its parent directory. Missing
    sections fall back to defaults.
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    retrieval = _build(RetrievalConfig, data.get("retrieval"))
    # [retrieval.vector] is a nested table; build it into a typed VectorConfig.
    retrieval.vector = _build(VectorConfig, (data.get("retrieval") or {}).get("vector"))
    return WikiConfig(
        root=path.parent,
        paths=_build(PathsConfig, data.get("paths")),
        frontmatter=_build(FrontmatterConfig, data.get("frontmatter")),
        grades=_build(GradesConfig, data.get("grades")),
        links=_build(LinksConfig, data.get("links")),
        citation=_build(CitationConfig, data.get("citation")),
        freshness=_build(FreshnessConfig, data.get("freshness")),
        graph=_build(GraphConfig, data.get("graph")),
        retrieval=retrieval,
        checks=_build(ChecksConfig, data.get("checks")),
        plugins=_build(PluginsConfig, data.get("plugins")),
        extra=data,
    )
