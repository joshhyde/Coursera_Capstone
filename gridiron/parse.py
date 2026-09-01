from __future__ import annotations

from typing import Any, Iterable, Iterator

from gridiron.constants import (
    FULL_GAME_MARKET_NAMES,
    FULL_GAME_PERIODS,
    MONEYLINE_TYPES,
    SPREAD_TYPES,
    TOTAL_TYPES,
)
from gridiron.models import Quote


def parse_quotes(payloads: Iterable[Any], catalog: Iterable[dict]) -> list[Quote]:
    index = _catalog_index(catalog)
    quotes: list[Quote] = []
    for fixture in _iter_fixtures(payloads):
        quotes.extend(_quotes_for_fixture(fixture, index))
    return quotes


def _catalog_index(catalog: Iterable[dict]) -> dict[int, dict]:
    return {int(row["marketId"]): row for row in catalog if "marketId" in row}


def _iter_fixtures(payloads: Iterable[Any]) -> Iterator[dict]:
    for payload in payloads:
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and item.get("fixtureId"):
                    yield item
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("fixtureId"):
            yield payload
            continue
        for key in ("data", "fixtures", "results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                for item in rows:
                    if isinstance(item, dict) and item.get("fixtureId"):
                        yield item
                break


def classify_market(meta: dict) -> str | None:
    if meta.get("playerProp") is True:
        return None
    name = meta.get("marketName") or ""
    if name in FULL_GAME_MARKET_NAMES:
        return FULL_GAME_MARKET_NAMES[name]
    period = str(meta.get("period") or "").lower()
    if period not in FULL_GAME_PERIODS:
        return None
    market_type = str(meta.get("marketType") or "").lower()
    if market_type in MONEYLINE_TYPES:
        return "moneyline"
    if market_type in SPREAD_TYPES:
        return "spread"
    if market_type in TOTAL_TYPES:
        return "total"
    return None


def _quotes_for_fixture(fixture: dict, catalog: dict[int, dict]) -> list[Quote]:
    fixture_id = str(fixture["fixtureId"])
    start_time = str(fixture.get("startTime") or "")
    home = str(fixture.get("participant1Name") or fixture.get("participant1Id") or "home")
    away = str(fixture.get("participant2Name") or fixture.get("participant2Id") or "away")
    quotes: list[Quote] = []
    books = fixture.get("bookmakerOdds") or {}
    if not isinstance(books, dict):
        return quotes
    for book, payload in books.items():
        if not isinstance(payload, dict) or payload.get("suspended"):
            continue
        markets = payload.get("markets") or {}
        if not isinstance(markets, dict):
            continue
        for market_id, market in markets.items():
            if not isinstance(market, dict) or market.get("marketActive") is False:
                continue
            try:
                mid = int(market_id)
            except (TypeError, ValueError):
                continue
            meta = catalog.get(mid)
            if meta is None:
                continue
            market_type = classify_market(meta)
            if market_type is None:
                continue
            period = str(meta.get("period") or "result")
            handicap = meta.get("handicap")
            line = None if market_type == "moneyline" else _as_float(handicap)
            outcomes = market.get("outcomes") or {}
            names = {
                int(o["outcomeId"]): str(o.get("outcomeName") or "")
                for o in meta.get("outcomes") or []
                if "outcomeId" in o
            }
            if not isinstance(outcomes, dict):
                continue
            for outcome_id, outcome in outcomes.items():
                if not isinstance(outcome, dict):
                    continue
                try:
                    oid = int(outcome_id)
                except (TypeError, ValueError):
                    continue
                side = _side(market_type, names.get(oid, ""), oid, mid)
                if side is None:
                    continue
                player = _game_player(outcome.get("players") or {})
                if player is None:
                    continue
                decimal = _as_float(player.get("price"))
                if decimal is None or decimal <= 1:
                    continue
                quotes.append(
                    Quote(
                        book=str(book),
                        market_type=market_type,
                        period=period,
                        line=line,
                        side=side,
                        decimal_odds=decimal,
                        american_odds=_american(player.get("priceAmerican"), decimal),
                        fixture_id=fixture_id,
                        start_time=start_time,
                        home=home,
                        away=away,
                        main_line=bool(player.get("mainLine")),
                    )
                )
    return quotes


def _game_player(players: Any) -> dict | None:
    if not isinstance(players, dict):
        return None
    for player in players.values():
        if not isinstance(player, dict):
            continue
        if player.get("playerName"):
            continue
        if player.get("active") is False:
            continue
        return player
    return None


def _side(market_type: str, name: str, outcome_id: int, market_id: int) -> str | None:
    label = name.strip().lower()
    if market_type == "total":
        if label.startswith("over") or label in {"o"}:
            return "Over"
        if label.startswith("under") or label in {"u"}:
            return "Under"
        return "Over" if outcome_id == market_id else "Under"
    if label in {"1", "home", "participant1"}:
        return "home"
    if label in {"2", "away", "participant2"}:
        return "away"
    if outcome_id == market_id:
        return "home"
    return "away"


def _american(raw: Any, decimal: float) -> int:
    if raw is not None and str(raw) != "":
        try:
            return int(str(raw).replace("+", "").replace(",", ""))
        except ValueError:
            pass
    if decimal >= 2:
        return int(round((decimal - 1) * 100))
    return int(round(-100 / (decimal - 1)))


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
