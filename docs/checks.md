# Checks

A **check** is a callable `(Wiki, WikiConfig) -> Iterable[Finding]` carrying an `id` and a
default `severity`. Built-in checks register at import; wiki-specific checks register via a
[plugin](extending.md).

Each finding has a **severity** — `error`, `warn`, or `info`. The `[checks].fail_on` list
(default `["error"]`) decides which severities make `pw check` exit nonzero; `[checks].disabled`
skips checks by id.

## Structural

Broken references, orphaned pages, and stale derived artifacts.

| Check id | Severity | Flags |
| --- | --- | --- |
| `broken-link` | error | A `[[wikilink]]` whose target slug has no page file. |
| `missing-page` | error | A slug declared in `CLAUDE.md` with no corresponding page. |
| `orphan-page` | warn | A page with no inbound links (unless listed under `[graph].roots`). |
| `stale-index` | error | The committed `index.md` differs from the freshly rendered one. |
| `missing-provenance` | error | A reference entry that names no real file under `raw/`. |

## Frontmatter

Required keys, declared types, and allowed vocabularies.

| Check id | Severity | Flags |
| --- | --- | --- |
| `frontmatter-parse` | error | Frontmatter block that fails to parse as YAML. |
| `frontmatter-required` | error | A required key (`[frontmatter].required`) missing from a page. |
| `frontmatter-type` | error | A key whose value violates its declared type in `[frontmatter].types`. |
| `tag-vocab` | warn | A tag outside the allowed `[frontmatter].tags` vocabulary (empty = any allowed). |

Declared types are one of `str`, `int`, `float`, `bool`, `list`, `date`.

## Citation integrity

The primary defense against hallucination-baking. Two parts:

| Check id | Severity | Flags |
| --- | --- | --- |
| `citation-resolution` | error | A `[n]` marker in prose that resolves to no reference entry. |
| `citation-coverage` | warn | A prose paragraph carrying no citation at all — a *candidate*, not a verdict. |

Provenance — whether a reference names a real `raw/` file — is enforced separately by the
`missing-provenance` structural check. Coverage lists candidates only; the code never judges
whether a given sentence is a factual claim.

## Source grades

Only enforced when a grade vocabulary is configured under `[grades].vocab`.

| Check id | Severity | Flags |
| --- | --- | --- |
| `grade-present` | error | A referenced source carrying no grade. |
| `grade-vocab` | error | A grade outside the fixed `[grades].vocab`. |
| `grade-surfaced` | warn | A page whose declared relied-on grade is not a real vocabulary value. |

## Graph

Derived from the deterministic link graph (explicit `[[wikilinks]]` only).

| Check id | Severity | Flags |
| --- | --- | --- |
| `phantom-hub` | warn | A heavily-linked target (`>= [graph].hub_min_inbound`) with no page. |
| `hub-stub` | warn | A hub whose body is shorter than `[graph].stub_max_chars`. |
| `fragile-bridge` | info | An articulation point — a page whose removal disconnects the graph. |

## Freshness

| Check id | Severity | Flags |
| --- | --- | --- |
| `stale-candidate` | info | A page whose recency marker is older than `[freshness].stale_after_days`. |

Freshness lists *candidates* only. It never judges whether a page's meaning is stale — that
is semantic and stays with the LLM.

All check behavior is tuned from [`wiki.toml`](configuration.md); no subject-matter knowledge
lives in any check.
