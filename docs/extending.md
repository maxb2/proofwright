# Extending

A universal invariant ships in the core `checks/` package. Anything **wiki-specific**
registers as a plugin — that is the "honest test of generality": if a rule needs
subject-matter knowledge, it does not belong in core.

## What a check is

A check is a callable `(Wiki, WikiConfig) -> Iterable[Finding]` carrying an `id` and a default
`severity`. A plugin exposes a `register(registry)` function that adds checks to the registry:

```python
# pw_provenance_plugin.py
from proofwright.report import Finding


def register(registry):
    @registry.register("frontmatter-sources", severity="error")
    def frontmatter_sources(wiki, cfg):
        # Plugins read their own config table via cfg.extra — core never touches it.
        conf = cfg.extra.get("frontmatter_sources", {})
        field = conf.get("field", "sources")
        require_for = set(conf.get("require_for", []))
        for page in wiki.pages:
            page_type = page.frontmatter.get("type")
            if page_type in require_for and not page.frontmatter.get(field):
                yield Finding(
                    check_id="frontmatter-sources",
                    severity="error",
                    message=f"{page.slug}: '{field}' provenance required for type '{page_type}'",
                )
```

## Two registration paths

### 1. Wiki-local modules — `[plugins] modules`

Dotted module paths, each exposing `register(registry)`. The wiki root is placed on
`sys.path`, so a plain file next to `wiki.toml` works by name:

```toml
[plugins]
modules = ["pw_provenance_plugin"]

# Plugins read arbitrary config tables via cfg.extra:
[frontmatter_sources]
field = "sources"
require_for = ["book"]
```

### 2. Installed packages — the `proofwright.checks` entry-point group

For third-party packages distributed on PyPI, register under the entry-point group. Each
entry point resolves to a `register(registry)` callable:

```toml
# pyproject.toml of your plugin package
[project.entry-points."proofwright.checks"]
my_checks = "my_package.checks:register"
```

These load automatically when `[plugins].load_entry_points` is `true` (the default).

## Notes

- Read plugin config from `cfg.extra` (the full parsed TOML). Core never reads these tables,
  so any structure you like is fair game.
- Choose a `severity` deliberately — only severities in `[checks].fail_on` break the build.
- A working example ships in the repository at `tests/fixtures/pw_provenance_plugin.py`.

See the [Plugins API](api/plugins.md) and [Checks API](api/checks.md) for the registry and
`Finding` types.
