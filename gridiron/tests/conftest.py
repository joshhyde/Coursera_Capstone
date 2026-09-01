from __future__ import annotations

import json
from pathlib import Path

import pytest

from gridiron.constants import BOOKS

FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture
def markets():
    return load_json("markets.json")


@pytest.fixture
def book_payloads():
    return [load_json(f"odds_nfl_{book}.json") for book in BOOKS]
