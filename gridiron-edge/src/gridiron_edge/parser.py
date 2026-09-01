from __future__ import annotations

from typing import Any

from gridiron_edge.models import GameOdds, Line
from gridiron_edge.storage import Storage


def _active_price(outcome: dict[str, Any]) -> dict[str, Any] | None:
    players = outcome.get("players", {})
    for player in players.values():
        if player.get("active"):
            return player
    return None


def _extract_main_lines(
    bookmaker_odds: dict[str, Any],
    storage: Storage,
) -> dict[str, dict[str, Line]]:
    markets = bookmaker_odds.get("markets", {})
    result: dict[str, dict[str, Line]] = {
        "moneyline": {},
        "spread": {},
        "total": {},
    }

    candidates: dict[str, list[tuple[str, Line, bool]]] = {
        "moneyline": [],
        "spread": [],
        "total": [],
    }

    for market_id_str, market_data in markets.items():
        market_id = int(market_id_str)
        mtype = storage.market_type(market_id)
        if not mtype:
            continue

        outcome_roles = storage.market_outcomes(market_id)
        outcomes = market_data.get("outcomes", {})

        for outcome_id, outcome_data in outcomes.items():
            price = _active_price(outcome_data)
            if not price:
                continue

            role = outcome_roles.get(str(outcome_id))
            if not role:
                continue

            meta_row = _market_meta(storage, market_id)
            handicap = meta_row.get("handicap") if meta_row else None
            line = Line(
                american=str(price["priceAmerican"]),
                decimal=float(price["price"]),
                handicap=float(handicap) if handicap is not None else None,
            )
            candidates[mtype].append((role, line, bool(price.get("mainLine"))))

    for mtype, items in candidates.items():
        if not items:
            continue
        main = [item for item in items if item[2]]
        chosen = main if main else items
        lines: dict[str, Line] = {}
        for role, line, _ in chosen:
            lines[role] = line
        if mtype == "moneyline" and "home" in lines and "away" in lines:
            result[mtype] = {"home": lines["home"], "away": lines["away"]}
        elif mtype == "spread" and "home" in lines and "away" in lines:
            result[mtype] = {"home": lines["home"], "away": lines["away"]}
        elif mtype == "total" and "over" in lines and "under" in lines:
            result[mtype] = {"over": lines["over"], "under": lines["under"]}

    return result


def _market_meta(storage: Storage, market_id: int) -> dict[str, Any]:
    with storage.connect() as conn:
        row = conn.execute(
            "SELECT market_type, market_name, handicap FROM market_meta WHERE market_id = ?",
            (market_id,),
        ).fetchone()
        return dict(row) if row else {}


def parse_fixture(
    payload: dict[str, Any],
    sport: str,
    storage: Storage,
) -> GameOdds:
    bookmakers = payload.get("bookmakerOdds", {})
    hr = bookmakers.get("hardrockbet", {})
    pin = bookmakers.get("pinnacle", {})

    hr_lines = _extract_main_lines(hr, storage) if hr else {"moneyline": {}, "spread": {}, "total": {}}
    pin_lines = _extract_main_lines(pin, storage) if pin else {"moneyline": {}, "spread": {}, "total": {}}

    hr_url = None
    if hr:
        hr_url = hr.get("fixturePath")

    return GameOdds(
        fixture_id=payload["fixtureId"],
        sport=sport,  # type: ignore[arg-type]
        home_team=payload.get("participant1Name", "Home"),
        away_team=payload.get("participant2Name", "Away"),
        start_time=payload.get("startTime", ""),
        hard_rock_url=hr_url,
        moneyline=hr_lines.get("moneyline") or None,
        spread=hr_lines.get("spread") or None,
        total=hr_lines.get("total") or None,
        pinnacle_moneyline=pin_lines.get("moneyline") or None,
        pinnacle_spread=pin_lines.get("spread") or None,
        pinnacle_total=pin_lines.get("total") or None,
    )


def sport_for_tournament(tournament_id: int, nfl_id: int, ncaa_id: int) -> str:
    if tournament_id == nfl_id:
        return "nfl"
    if tournament_id == ncaa_id:
        return "cfb"
    return "unknown"
