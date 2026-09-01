import json
from pathlib import Path

from gridiron.parse import classify_market, parse_quotes

FIXTURES = Path(__file__).parent / "fixtures"


def test_classify_full_game_names(markets):
    by_id = {row["marketId"]: row for row in markets}
    assert classify_market(by_id[141]) == "moneyline"
    assert classify_market(by_id[14272]) == "spread"
    assert classify_market(by_id[1464]) == "total"
    assert classify_market(by_id[113]) is None
    assert classify_market(by_id[9001]) is None
    assert classify_market(by_id[14388]) is None


def test_parse_quotes_keeps_game_lines_and_drops_props(markets, book_payloads):
    quotes = parse_quotes(book_payloads, markets)
    assert quotes
    assert all(q.market_type in {"moneyline", "spread", "total"} for q in quotes)
    assert all(q.book for q in quotes)
    assert {q.fixture_id for q in quotes} == {
        "id1400003171515752",
        "id1400003171515753",
    }
    assert any(q.line == -4 and q.book == "hardrockbet" for q in quotes)
    assert all(q.period != "p1" for q in quotes)
    names = {(q.home, q.away) for q in quotes}
    assert ("New England Patriots", "Seattle Seahawks") in names


def test_parse_reads_recorded_hardrock_payload_alone(markets):
    payload = json.loads((FIXTURES / "odds_nfl_hardrockbet.json").read_text(encoding="utf-8"))
    quotes = parse_quotes([payload], markets)
    hr = [q for q in quotes if q.book == "hardrockbet" and q.market_type == "moneyline"]
    home = next(q for q in hr if q.side == "home" and q.fixture_id.endswith("752"))
    assert home.decimal_odds == 2.2
    assert home.american_odds == 120
    assert home.main_line is True
