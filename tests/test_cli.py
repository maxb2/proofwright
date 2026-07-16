import json

from proofwright.cli import main

from conftest import BROKEN, GOOD


def test_check_good_exit_zero(capsys):
    code = main(["check", "--config", str(GOOD / "wiki.toml")])
    assert code == 0
    assert "no findings" in capsys.readouterr().out


def test_check_broken_exit_one_json(capsys):
    code = main(["check", "--config", str(BROKEN / "wiki.toml"), "--format", "json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["counts"]["error"] == 3
    ids = {f["check_id"] for f in payload["findings"]}
    assert "broken-link" in ids


def test_lint_is_alias_for_check(capsys):
    assert main(["lint", "--config", str(GOOD / "wiki.toml")]) == 0


def test_index_check_broken_exit_one(capsys):
    assert main(["index", "--config", str(BROKEN / "wiki.toml"), "--check"]) == 1
