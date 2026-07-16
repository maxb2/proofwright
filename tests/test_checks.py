from proofwright import run_checks


def test_good_wiki_is_clean(good_config):
    _, report = run_checks(good_config)
    assert report.findings == []
    assert report.exit_code(good_config.checks.fail_on) == 0


def test_broken_wiki_findings(broken_config):
    _, report = run_checks(broken_config)
    ids = {f.check_id for f in report.findings}
    assert ids == {
        "stale-index",
        "grade-vocab",
        "broken-link",
        "orphan-page",
        "citation-coverage",
    }
    assert report.counts() == {"error": 3, "warn": 2, "info": 0}
    assert report.exit_code(broken_config.checks.fail_on) == 1


def test_broken_link_location(broken_config):
    _, report = run_checks(broken_config)
    bl = next(f for f in report.findings if f.check_id == "broken-link")
    assert bl.path == "wiki/page-a.md"
    assert bl.line == 8
    assert bl.data["target"] == "ghost"


def test_disabled_check_is_skipped(broken_config):
    broken_config.checks.disabled = ["grade-vocab"]
    _, report = run_checks(broken_config)
    assert "grade-vocab" not in {f.check_id for f in report.findings}
