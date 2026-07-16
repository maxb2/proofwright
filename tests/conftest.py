import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = FIXTURES / "mini-wiki-good"
BROKEN = FIXTURES / "mini-wiki-broken"


@pytest.fixture
def good_config():
    from proofwright import load_config

    return load_config(GOOD / "wiki.toml")


@pytest.fixture
def broken_config():
    from proofwright import load_config

    return load_config(BROKEN / "wiki.toml")


@pytest.fixture
def good_copy(tmp_path):
    """A writable copy of the good fixture (for index --write round-trips)."""
    dest = tmp_path / "wiki"
    shutil.copytree(GOOD, dest)
    return dest
