{#-
  Hierarchical (folder-grouped) index. Point `[paths] index_template` at this file to
  group links by folder under headings instead of one flat list — this keeps the index
  small for the query agent: it reads section headings first and descends only the
  relevant branch, rather than pulling every link into context on every query.

  `link_tree` is recursive: each group has `heading`, `entries` (pre-rendered link lines),
  and `subgroups` (child folders). Root-level pages appear under an `Overview` heading.
  Edit the prose below freely; the {% ... %} blocks are what generate the link sections.
-#}
{%- macro section(group, level) -%}
{{ "#" * level }} {{ group.heading }}

{% for entry in group.entries %}
{{ entry }}
{% endfor %}
{% for sub in group.subgroups %}

{{ section(sub, level + 1) }}
{%- endfor %}
{%- endmacro -%}
# Index

This wiki is organized into the sections below. Replace this paragraph with a short
description of what the wiki covers and how it is structured.

{% for group in link_tree.subgroups %}
{{ section(group, 2) }}
{% endfor %}
