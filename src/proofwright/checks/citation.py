"""Citation integrity — the primary defense against hallucination-baking.

Two parts:

* **resolution** (``error``): every ``[n]`` marker in prose resolves to a reference entry.
  Provenance (does the reference name a real ``raw/`` file) is enforced separately by the
  ``missing-provenance`` structural check.
* **coverage** (``warn``): prose paragraphs that carry no citation at all. This flags
  *candidates* — code lists them, it does not judge whether a sentence is a factual claim.
"""

from __future__ import annotations

from ..config import WikiConfig
from ..model import Wiki
from ..report import Finding
from . import registry, rel

# Paragraph lines that never need a citation on their own.
_STRUCTURAL_PREFIXES = ("#", ">", "|", "```", "- ", "* ", "+ ", "1.")


@registry.register("citation-resolution", severity="error")
def citation_resolution(wiki: Wiki, cfg: WikiConfig):
    for page in wiki.pages:
        for cite in page.citations:
            if cite.source is None:
                yield Finding(
                    check_id="citation-resolution",
                    severity="error",
                    message=f"citation [{cite.marker}] has no matching reference entry",
                    path=rel(wiki, page.path),
                    line=cite.line,
                    data={"marker": cite.marker},
                )


@registry.register("citation-coverage", severity="warn")
def citation_coverage(wiki: Wiki, cfg: WikiConfig):
    if cfg.citation.claim_policy == "off":
        return
    for page in wiki.pages:
        cited_lines = {c.line for c in page.citations}
        for para in _paragraphs(page):
            if any(line in cited_lines for line in para["lines"]):
                continue
            yield Finding(
                check_id="citation-coverage",
                severity="warn",
                message="prose paragraph has no citation",
                path=rel(wiki, page.path),
                line=para["start"],
                data={"text": para["text"][:80]},
            )


def _paragraphs(page):
    """Yield prose paragraphs from the body as {start, lines, text}.

    A paragraph is a run of consecutive non-blank prose lines. Skips headings, lists,
    quotes, tables, and code fences. ``page.lines`` are body lines; ``page.body_start``
    maps body offset 0 to its 1-based file line.
    """
    from ..parse import HEADING_RE

    para_lines: list[int] = []
    para_text: list[str] = []
    in_code = False
    results = []

    def flush():
        if para_lines:
            results.append(
                {
                    "start": para_lines[0],
                    "lines": list(para_lines),
                    "text": " ".join(para_text).strip(),
                }
            )
        para_lines.clear()
        para_text.clear()

    for offset, raw in enumerate(page.lines):
        file_line = page.body_start + offset
        if file_line in page.ref_lines:  # references block is not prose to cite
            flush()
            continue
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            flush()
            continue
        if in_code:
            continue
        if not stripped:
            flush()
            continue
        if HEADING_RE.match(raw) or stripped.startswith(_STRUCTURAL_PREFIXES):
            flush()
            continue
        para_lines.append(file_line)
        para_text.append(stripped)
    flush()
    return results
