"""Frontmatter checks: required keys, declared types, allowed tag/grade vocabularies."""

from __future__ import annotations

import datetime as _dt

from ..config import WikiConfig
from ..model import Wiki
from ..report import Finding
from . import registry, rel

_TYPE_CHECKS = {
    "str": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, list),
    "date": lambda v: isinstance(v, (_dt.date, _dt.datetime)),
}


@registry.register("frontmatter-required", severity="error")
def required_keys(wiki: Wiki, cfg: WikiConfig):
    index_slug = cfg.index_slug()
    for page in wiki.pages:
        if page.slug == index_slug:  # index is a generated artifact, not a curated page
            continue
        for key in cfg.frontmatter.required:
            if key not in page.frontmatter:
                yield Finding(
                    check_id="frontmatter-required",
                    severity="error",
                    message=f"missing required frontmatter key '{key}'",
                    path=rel(wiki, page.path),
                    line=1,
                    data={"key": key},
                )


@registry.register("frontmatter-type", severity="error")
def key_types(wiki: Wiki, cfg: WikiConfig):
    for page in wiki.pages:
        for key, type_name in cfg.frontmatter.types.items():
            if key not in page.frontmatter:
                continue
            predicate = _TYPE_CHECKS.get(type_name)
            if predicate and not predicate(page.frontmatter[key]):
                yield Finding(
                    check_id="frontmatter-type",
                    severity="error",
                    message=f"frontmatter key '{key}' should be {type_name}",
                    path=rel(wiki, page.path),
                    line=1,
                    data={"key": key, "expected": type_name},
                )


@registry.register("tag-vocab", severity="warn")
def tag_vocab(wiki: Wiki, cfg: WikiConfig):
    allowed = set(cfg.frontmatter.tags)
    if not allowed:
        return
    field = cfg.frontmatter.tags_field
    for page in wiki.pages:
        tags = page.frontmatter.get(field, [])
        if not isinstance(tags, list):
            tags = [tags]
        for tag in tags:
            if tag not in allowed:
                yield Finding(
                    check_id="tag-vocab",
                    severity="warn",
                    message=f"tag '{tag}' not in allowed vocabulary",
                    path=rel(wiki, page.path),
                    line=1,
                    data={"tag": tag},
                )
