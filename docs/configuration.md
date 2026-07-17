# Configuration

All per-wiki variance lives in a declarative `wiki.toml` — paths, vocabularies, thresholds,
and policies. It loads into a typed [`WikiConfig`](api/config.md), with sensible defaults so a
wiki works with a near-empty file. The directory holding `wiki.toml` is the **wiki root**;
every path resolves relative to it.

## Sections

### `[paths]`
Where things live. `raw` (immutable sources), `wiki` (LLM-owned pages), `schema` (the
`CLAUDE.md` conventions file whose declared `[[slugs]]` must have page files), and `index`
(the generated table of contents). Set `index_template` to a Jinja2 template (receiving
`links` and `link_tree`) for a custom index; unset means the built-in flat list.

### `[links]`
`style` sets how cross-references are written: `wikilink` (`[[slug]]`, Obsidian style),
`markdown` (`[label](path.md)`), or `both` (accept either).

### `[frontmatter]`
`required` keys every page must carry; `types` maps a key to one of
`str|int|float|bool|list|date`; `tags` is the allowed tag vocabulary (`[]` = any). `tags_field`
and `grade_field` name the frontmatter keys holding tags and the relied-on source grade.

### `[grades]`
`vocab` is the fixed reliability-grade vocabulary. Empty means grading is not enforced.

### `[citation]`
`references` = how `[n]` maps to a source (`section` = a References section of
`[n]. <text naming a raw/ path or url>` lines); `references_heading` names that section;
`claim_policy` = `paragraph` flags uncited prose, `off` disables coverage flagging.

### `[freshness]`
`recency_field` (frontmatter key holding the date) and `stale_after_days` (the staleness
threshold for the `stale-candidate` triage list).

### `[graph]`
`roots` = slugs allowed to have no inbound links (entry points); `hub_min_inbound` = inbound
count that makes a page a hub; `stub_max_chars` = a hub shorter than this is a "hub stub".

### `[retrieval]` and `[retrieval.vector]`
Tuning for `pw search`. See the dedicated [Retrieval](retrieval.md) page for what each knob
does and how the streams fuse.

### `[checks]`
`fail_on` = severities that cause a nonzero exit code (default `["error"]`); `disabled` = check
ids to skip.

### `[plugins]`
`modules` = dotted module paths exposing `register(registry)` (the wiki root is on
`sys.path`, so a wiki-local plugin file works by name); `load_entry_points` toggles loading
the `proofwright.checks` entry-point group. See [Extending](extending.md).

Plugins read their own arbitrary config tables via `cfg.extra` — core never reads them.

## Full annotated example

The starter config, straight from the repository (`templates/wiki.toml.example`):

```toml
--8<-- "templates/wiki.toml.example"
```
