"""Freshness triage.

Code lists *candidates* only: pages whose recency marker is older than a configured
threshold. It never judges whether the page's *meaning* is stale — that is semantic and
stays with the LLM. Emitted as ``info``.
"""

from __future__ import annotations

import datetime as _dt

from ..config import WikiConfig
from ..model import Wiki
from ..report import Finding
from . import registry, rel


def _as_date(value) -> _dt.date | None:
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


@registry.register("stale-candidate", severity="info")
def stale_candidates(wiki: Wiki, cfg: WikiConfig):
    field = cfg.freshness.recency_field
    horizon = _dt.date.today() - _dt.timedelta(days=cfg.freshness.stale_after_days)
    for page in wiki.pages:
        raw = page.frontmatter.get(field)
        date = _as_date(raw)
        if date is not None and date < horizon:
            yield Finding(
                check_id="stale-candidate",
                severity="info",
                message=f"page not updated since {date.isoformat()} (staleness candidate)",
                path=rel(wiki, page.path),
                line=1,
                data={"updated": date.isoformat()},
            )
