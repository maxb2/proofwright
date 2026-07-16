"""Findings and reports.

JSON is the machine-readable core output; text is a convenience renderer for terminals.
The CI exit-code policy (which severities count as failure) lives in
``WikiConfig.checks.fail_on``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

SEVERITIES = ("error", "warn", "info")


@dataclass
class Finding:
    check_id: str
    severity: str  # one of SEVERITIES
    message: str
    path: str | None = None  # repo-relative path
    line: int | None = None
    data: dict = field(default_factory=dict)

    def location(self) -> str:
        if self.path and self.line:
            return f"{self.path}:{self.line}"
        return self.path or "-"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def extend(self, findings) -> None:
        self.findings.extend(findings)

    def counts(self) -> dict[str, int]:
        counts = {s: 0 for s in SEVERITIES}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    def failed(self, fail_on: list[str]) -> bool:
        return any(f.severity in fail_on for f in self.findings)

    def exit_code(self, fail_on: list[str]) -> int:
        return 1 if self.failed(fail_on) else 0

    # --- renderers ---------------------------------------------------------------
    def to_json(self) -> str:
        payload = {
            "findings": [asdict(f) for f in self.findings],
            "counts": self.counts(),
        }
        return json.dumps(payload, indent=2, sort_keys=False)

    def to_text(self, root: Path | None = None) -> str:
        if not self.findings:
            return "OK — no findings."
        order = {s: i for i, s in enumerate(SEVERITIES)}
        icon = {"error": "✗", "warn": "!", "info": "·"}
        lines = []
        for f in sorted(self.findings, key=lambda x: (order.get(x.severity, 9), x.location())):
            lines.append(
                f"{icon.get(f.severity, '?')} {f.severity:5} {f.location()}  "
                f"[{f.check_id}] {f.message}"
            )
        c = self.counts()
        lines.append("")
        lines.append(f"{c['error']} error, {c['warn']} warn, {c['info']} info")
        return "\n".join(lines)
