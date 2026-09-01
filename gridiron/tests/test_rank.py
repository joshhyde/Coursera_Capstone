import pytest

from gridiron.constants import JSON_PICK_KEYS, TARGET_BOOK
from gridiron.parse import parse_quotes
from gridiron.rank import _main_line_quotes, rank_picks


def _picks(markets, book_payloads, min_ev=0.0):
    quotes = parse_quotes(book_payloads, markets)
    return rank_picks(quotes, league="nfl", min_ev=min_ev)


def test_ranks_hard_rock_plus_ev_and_drops_minus_ev(markets, book_payloads):
    picks = _picks(markets, book_payloads)
    assert picks
    assert picks == sorted(picks, key=lambda p: -p.ev)
    assert all(p.ev > 0 for p in picks)
    assert all(p.quote.book == "hardrockbet" for p in picks)
    patriots_ml = next(
        p
        for p in picks
        if p.quote.market_type == "moneyline"
        and p.quote.side == "home"
        and p.quote.home == "New England Patriots"
    )
    assert patriots_ml.ev == pytest.approx(0.1)
    assert patriots_ml.fair.source == "pinnacle"
    assert patriots_ml.books_used == ("pinnacle",)
    assert patriots_ml.disagreement


def test_json_payload_has_required_keys(markets, book_payloads):
    payload = _picks(markets, book_payloads)[0].as_json()
    assert tuple(payload) == JSON_PICK_KEYS


def test_uses_consensus_when_pinnacle_missing(markets, book_payloads):
    chiefs = [
        p
        for p in _picks(markets, book_payloads)
        if p.quote.home == "Kansas City Chiefs" and p.quote.market_type == "moneyline"
    ]
    assert chiefs
    assert all(p.fair.source == "consensus" for p in chiefs)
    assert "pinnacle" not in chiefs[0].books_used
    assert "draftkings" in chiefs[0].books_used


def test_main_line_only_drops_alternate_spread(markets, book_payloads):
    quotes = parse_quotes(book_payloads, markets)
    mains = _main_line_quotes(quotes, TARGET_BOOK)
    spreads = [
        q
        for q in mains
        if q.market_type == "spread" and q.home == "New England Patriots"
    ]
    assert spreads
    assert all(q.line == -3.5 for q in spreads)
    assert all(not (p.quote.market_type == "spread" and p.quote.line == -4) for p in _picks(markets, book_payloads))


def test_min_ev_filters(markets, book_payloads):
    wide = _picks(markets, book_payloads, min_ev=0.0)
    tight = _picks(markets, book_payloads, min_ev=0.15)
    assert len(tight) < len(wide)
    assert all(p.ev > 0.15 for p in tight)
