import json

from pathlib import Path

from gridiron.cli import MISSING_KEY, main
from gridiron.client import OddsClient
from gridiron.constants import JSON_PICK_KEYS


def test_missing_key_exits_nonzero(monkeypatch, capsys):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.setattr("gridiron.cli._load_dotenv", lambda: None)
    code = main(["picks", "--league", "nfl"])
    captured = capsys.readouterr()
    assert code != 0
    assert ENV_FRAGMENT in captured.err
    assert "ODDS_API_KEY is not set" in captured.err
    assert captured.out == ""


ENV_FRAGMENT = MISSING_KEY.split(".", 1)[0]


def test_json_emits_required_keys(monkeypatch, capsys, markets, book_payloads):
    monkeypatch.setenv("ODDS_API_KEY", "test-key-not-real")
    monkeypatch.setattr(OddsClient, "fetch_markets", lambda self: markets)
    monkeypatch.setattr(
        OddsClient,
        "fetch_league_odds",
        lambda self, league: book_payloads,
    )
    code = main(["picks", "--league", "nfl", "--json"])
    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert isinstance(payload, list)
    assert payload
    for row in payload:
        assert tuple(row) == JSON_PICK_KEYS
        assert row["ev"] > 0
        assert row["league"] == "nfl"


def test_table_prints_ranked_picks(monkeypatch, capsys, markets, book_payloads):
    monkeypatch.setenv("ODDS_API_KEY", "test-key-not-real")
    monkeypatch.setattr(OddsClient, "fetch_markets", lambda self: markets)
    monkeypatch.setattr(
        OddsClient,
        "fetch_league_odds",
        lambda self, league: book_payloads,
    )
    code = main(["picks", "--league", "nfl", "--limit", "3"])
    captured = capsys.readouterr()
    assert code == 0
    assert "EV" in captured.out
    assert "Selection" in captured.out
    assert captured.out.count("\n") >= 3


def test_fixtures_are_recorded_json_not_live_network():
    path = Path(__file__).parent / "fixtures" / "odds_nfl_hardrockbet.json"
    hardrock = json.loads(path.read_text(encoding="utf-8"))
    assert hardrock[0]["bookmakerOdds"]["hardrockbet"]
    assert "api.oddspapi.io" not in json.dumps(hardrock)
