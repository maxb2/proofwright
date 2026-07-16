"""Parsing: markdown + frontmatter → the :mod:`proofwright.model` types.

Deliberately regex/line based and content-agnostic — no markdown engine, no semantic
understanding. Every extracted item carries a 1-based line number so findings can point at
``path:line``.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .config import WikiConfig
from .model import Citation, Page, Source, Wiki, WikiLink

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")
# A markdown link [label](target); the leading (?<!!) skips images ![alt](src).
MDLINK_RE = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:")  # http:, https:, mailto:, etc.
# A [n] citation marker: bracketed digits, not a [[wikilink]] and not a [text](link).
CITATION_RE = re.compile(r"(?<!\[)\[(\d+)\](?![\](])")
# A reference list entry: "[3]. text" or "3. text".
REFERENCE_RE = re.compile(r"^\s*\[?(\d+)\]?\.\s+(.*)$")
RAW_PATH_RE = re.compile(r"(?:\./)?(?:raw/)?[\w./-]+\.(?:md|txt|pdf|html|htm)")
URL_RE = re.compile(r"https?://\S+")
GRADE_RE = re.compile(r"grade:\s*([^\s)\]]+)", re.IGNORECASE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def slug_for(path: Path, wiki_dir: Path) -> str:
    """Derive a page slug from its path relative to the wiki dir (posix, no extension)."""
    rel = path.relative_to(wiki_dir).with_suffix("")
    return rel.as_posix()


def resolve_md_target(target: str, page_dir: Path, wiki_dir: Path) -> str | None:
    """Resolve a markdown link target to an internal page slug, or None.

    Returns None for external URLs, in-page anchors, and targets that resolve outside
    the wiki directory (e.g. ``../../raw/...`` provenance links) — those are not graph
    edges between pages.
    """
    target = target.strip()
    if " " in target:  # drop an optional link title: (path "Title")
        target = target.split(" ", 1)[0]
    target = target.split("#", 1)[0]  # drop anchor
    if not target or target.startswith("#"):
        return None
    if _SCHEME_RE.match(target):
        return None  # external URL / mailto
    abs_path = (page_dir / target).resolve()
    try:
        rel = abs_path.relative_to(wiki_dir.resolve())
    except ValueError:
        return None  # outside wiki/ (provenance or external file)
    return rel.with_suffix("").as_posix()


def extract_links(line: str, file_line: int, page_dir: Path, wiki_dir: Path, cfg) -> list:
    """Extract wikilinks and/or markdown links from one line per the configured style."""
    out: list[WikiLink] = []
    style = cfg.links.style
    if style in ("wikilink", "both"):
        for m in WIKILINK_RE.finditer(line):
            out.append(
                WikiLink(
                    target_slug=m.group(1).strip(),
                    line=file_line,
                    raw=m.group(0),
                    label=(m.group(2).strip() if m.group(2) else None),
                )
            )
    if style in ("markdown", "both"):
        for m in MDLINK_RE.finditer(line):
            slug = resolve_md_target(m.group(2), page_dir, wiki_dir)
            if slug is None:
                continue
            out.append(
                WikiLink(
                    target_slug=slug,
                    line=file_line,
                    raw=m.group(0),
                    label=m.group(1).strip(),
                )
            )
    return out


def split_frontmatter(text: str) -> tuple[dict, str, int, str | None]:
    """Return (frontmatter, body, body_start_line, error).

    ``body_start_line`` is the 1-based line number in the original file where the body
    begins. ``error`` is a YAML parse-error message when the frontmatter block is present
    but invalid, else None — so a parse failure is reported honestly rather than silently
    blanking the frontmatter.
    """
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = re.search(r"\n---[ \t]*\r?\n", text)
        if end:
            fm_text = text[4 : end.start() + 1]
            error = None
            try:
                fm = yaml.safe_load(fm_text) or {}
            except yaml.YAMLError as exc:
                fm, error = {}, str(exc).replace("\n", " ")
            if not isinstance(fm, dict):
                fm, error = {}, error or "frontmatter is not a mapping"
            body = text[end.end() :]
            body_start = text[: end.end()].count("\n") + 1
            return fm, body, body_start, error
    return {}, text, 1, None


def _find_references_start(body_lines: list[str], heading: str) -> int | None:
    """Index into ``body_lines`` of the first reference entry, or None."""
    target = heading.strip().lower()
    for i, line in enumerate(body_lines):
        m = HEADING_RE.match(line)
        if m and m.group(1).strip().lower() == target:
            return i + 1
    return None


def parse_references(
    body_lines: list[str], ref_start: int, body_start_line: int
) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for offset in range(ref_start, len(body_lines)):
        line = body_lines[offset]
        if HEADING_RE.match(line):  # next section ends the references block
            break
        m = REFERENCE_RE.match(line)
        if not m:
            continue
        key, text = m.group(1), m.group(2).strip()
        raw_m = RAW_PATH_RE.search(text)
        url_m = URL_RE.search(text)
        grade_m = GRADE_RE.search(text)
        sources[key] = Source(
            id=key,
            text=text,
            raw_path=raw_m.group(0).lstrip("./") if raw_m else None,
            url=url_m.group(0) if url_m else None,
            grade=grade_m.group(1) if grade_m else None,
        )
    return sources


def parse_page(path: Path, wiki_dir: Path, cfg: WikiConfig) -> Page:
    text = path.read_text(encoding="utf-8")
    fm, body, body_start_line, fm_error = split_frontmatter(text)
    body_lines = body.splitlines()

    ref_start = _find_references_start(body_lines, cfg.citation.references_heading)
    sources = (
        parse_references(body_lines, ref_start, body_start_line) if ref_start is not None else {}
    )
    # Body offsets that belong to the references block (excluded from citation scanning).
    ref_line_set = set(range(ref_start, len(body_lines))) if ref_start is not None else set()
    # Same block expressed as 1-based file lines (for claim-coverage exclusion).
    ref_file_lines = {body_start_line + off for off in ref_line_set}

    links: list[WikiLink] = []
    citations: list[Citation] = []
    for offset, line in enumerate(body_lines):
        file_line = body_start_line + offset
        links.extend(extract_links(line, file_line, path.parent, wiki_dir, cfg))
        if offset in ref_line_set:
            continue
        for m in CITATION_RE.finditer(line):
            citations.append(Citation(marker=m.group(1), line=file_line))

    # Resolve citations against this page's own reference table.
    for cite in citations:
        cite.source = sources.get(cite.marker)

    return Page(
        path=path,
        slug=slug_for(path, wiki_dir),
        frontmatter=fm,
        body=body,
        lines=body_lines,
        body_start=body_start_line,
        links=links,
        citations=citations,
        sources=sources,
        ref_lines=ref_file_lines,
        fm_error=fm_error,
    )


def _load_raw_inventory(cfg: WikiConfig) -> set[str]:
    raw_dir = cfg.raw_dir
    if not raw_dir.exists():
        return set()
    files: set[str] = set()
    for p in raw_dir.rglob("*"):
        if p.is_file():
            files.add(p.relative_to(cfg.root).as_posix())
    return files


def _load_schema_slugs(cfg: WikiConfig) -> list[str]:
    """Declared/expected page slugs = links found in the schema file (per link style)."""
    schema = cfg.schema_path
    if not schema.exists():
        return []
    slugs: list[str] = []
    for i, line in enumerate(schema.read_text(encoding="utf-8").splitlines(), start=1):
        for link in extract_links(line, i, schema.parent, cfg.wiki_dir, cfg):
            slugs.append(link.target_slug)
    return slugs


def load_wiki(cfg: WikiConfig) -> Wiki:
    wiki_dir = cfg.wiki_dir
    pages: list[Page] = []
    if wiki_dir.exists():
        for path in sorted(wiki_dir.rglob("*.md")):
            pages.append(parse_page(path, wiki_dir, cfg))
    wiki = Wiki(
        root=cfg.root,
        pages=pages,
        raw_files=_load_raw_inventory(cfg),
        schema_slugs=_load_schema_slugs(cfg),
    )
    wiki.index_pages()
    return wiki
