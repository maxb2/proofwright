"""Source-grade consistency.

Only enforced when a grade vocabulary is configured. Checks that every referenced source
carries a grade, that the grade is in the fixed vocabulary, and (if the page declares a
relied-on grade in frontmatter) that it is a real vocabulary value.
"""

from __future__ import annotations

from ..config import WikiConfig
from ..model import Wiki
from ..report import Finding
from . import registry, rel


@registry.register("grade-present", severity="error")
def grade_present(wiki: Wiki, cfg: WikiConfig):
    if not cfg.grades.vocab:
        return
    for page in wiki.pages:
        for marker, source in page.sources.items():
            if source.grade is None:
                yield Finding(
                    check_id="grade-present",
                    severity="error",
                    message=f"reference [{marker}] has no reliability grade",
                    path=rel(wiki, page.path),
                    line=1,
                    data={"marker": marker},
                )


@registry.register("grade-vocab", severity="error")
def grade_vocab(wiki: Wiki, cfg: WikiConfig):
    vocab = set(cfg.grades.vocab)
    if not vocab:
        return
    for page in wiki.pages:
        for marker, source in page.sources.items():
            if source.grade is not None and source.grade not in vocab:
                yield Finding(
                    check_id="grade-vocab",
                    severity="error",
                    message=f"reference [{marker}] grade '{source.grade}' not in vocabulary",
                    path=rel(wiki, page.path),
                    line=1,
                    data={"marker": marker, "grade": source.grade},
                )


@registry.register("grade-surfaced", severity="warn")
def grade_surfaced(wiki: Wiki, cfg: WikiConfig):
    """If a page surfaces a relied-on grade in frontmatter, it must be a vocab value."""
    vocab = set(cfg.grades.vocab)
    if not vocab:
        return
    field = cfg.frontmatter.grade_field
    for page in wiki.pages:
        if field not in page.frontmatter:
            continue
        value = page.frontmatter[field]
        if value not in vocab:
            yield Finding(
                check_id="grade-surfaced",
                severity="warn",
                message=f"frontmatter '{field}' value '{value}' not in grade vocabulary",
                path=rel(wiki, page.path),
                line=1,
                data={"grade": value},
            )
