from __future__ import annotations

from gridiron_edge.models import GameOdds, Line, MarketType, Pick, Side
from gridiron_edge.odds_math import (
    american_to_decimal,
    american_to_implied_prob,
    confidence_label,
    edge_pct,
    remove_vig,
)


def _fair_probs_from_pinnacle(
    pin_home: Line,
    pin_away: Line,
) -> tuple[float, float]:
    p_home = american_to_implied_prob(pin_home.american)
    p_away = american_to_implied_prob(pin_away.american)
    return remove_vig(p_home, p_away)


def _evaluate_two_way(
    game: GameOdds,
    market: MarketType,
    hr_lines: dict[str, Line],
    pin_lines: dict[str, Line],
    keys: tuple[str, str],
    labels: tuple[str, str],
    min_edge: float,
    stake: float,
) -> list[Pick]:
    picks: list[Pick] = []
    if not hr_lines or not pin_lines:
        return picks

    fair_home, fair_away = _fair_probs_from_pinnacle(
        pin_lines[keys[0]], pin_lines[keys[1]]
    )
    sides = [
        (keys[0], labels[0], fair_home, hr_lines[keys[0]]),
        (keys[1], labels[1], fair_away, hr_lines[keys[1]]),
    ]

    for side_key, label, fair_prob, hr_line in sides:
        dec = american_to_decimal(hr_line.american)
        edge = edge_pct(fair_prob, dec)
        if edge < min_edge or edge > 20.0:
            continue
        picks.append(
            Pick(
                fixture_id=game.fixture_id,
                sport=game.sport,
                home_team=game.home_team,
                away_team=game.away_team,
                start_time=game.start_time,
                market=market,
                side=Side.HOME if side_key == "home" else Side.AWAY if market != MarketType.TOTAL else Side.OVER,
                selection=label,
                hard_rock_line=hr_line,
                fair_line=Line(
                    american=_prob_to_american(fair_prob),
                    decimal=1.0 / fair_prob if fair_prob > 0 else 99.0,
                    handicap=hr_line.handicap,
                ),
                edge_pct=round(edge, 2),
                stake_usd=stake,
                confidence=confidence_label(edge),
                hard_rock_url=game.hard_rock_url,
                reason=f"Pinnacle fair prob {fair_prob*100:.1f}% vs Hard Rock {hr_line.american}",
            )
        )
    return picks


def _prob_to_american(prob: float) -> str:
    if prob <= 0 or prob >= 1:
        return "+100"
    if prob >= 0.5:
        return str(int(round(-100 * prob / (1 - prob))))
    return f"+{int(round(100 * (1 - prob) / prob))}"


def generate_picks(
    games: list[GameOdds],
    *,
    min_edge_pct: float = 2.0,
    stake_usd: float = 5.0,
) -> list[Pick]:
    all_picks: list[Pick] = []

    for game in games:
        if game.moneyline and game.pinnacle_moneyline:
            for p in _evaluate_moneyline(game, min_edge_pct, stake_usd):
                all_picks.append(p)
        if game.spread and game.pinnacle_spread:
            for p in _evaluate_spread(game, min_edge_pct, stake_usd):
                all_picks.append(p)
        if game.total and game.pinnacle_total:
            for p in _evaluate_total(game, min_edge_pct, stake_usd):
                all_picks.append(p)

    all_picks.sort(key=lambda p: p.edge_pct, reverse=True)
    return all_picks


def _evaluate_moneyline(game: GameOdds, min_edge: float, stake: float) -> list[Pick]:
    assert game.moneyline and game.pinnacle_moneyline
    picks = _evaluate_two_way(
        game,
        MarketType.MONEYLINE,
        game.moneyline,
        game.pinnacle_moneyline,
        ("home", "away"),
        (game.home_team, game.away_team),
        min_edge,
        stake,
    )
    for p in picks:
        if p.selection == game.home_team:
            p.side = Side.HOME
        else:
            p.side = Side.AWAY
    return picks


def _evaluate_spread(game: GameOdds, min_edge: float, stake: float) -> list[Pick]:
    assert game.spread and game.pinnacle_spread
    hr_home = game.spread["home"]
    pin_home = game.pinnacle_spread["home"]
    if hr_home.handicap is None or pin_home.handicap is None:
        return []
    if abs(hr_home.handicap - pin_home.handicap) > 0.01:
        return []

    hcap = hr_home.handicap
    home_label = f"{game.home_team} {hcap:+.1f}"
    away_hcap = -hcap
    away_label = f"{game.away_team} {away_hcap:+.1f}"
    picks = _evaluate_two_way(
        game,
        MarketType.SPREAD,
        game.spread,
        game.pinnacle_spread,
        ("home", "away"),
        (home_label, away_label),
        min_edge,
        stake,
    )
    for p in picks:
        if p.selection.startswith(game.home_team):
            p.side = Side.HOME
        else:
            p.side = Side.AWAY
    return picks


def _evaluate_total(game: GameOdds, min_edge: float, stake: float) -> list[Pick]:
    assert game.total and game.pinnacle_total
    hr_over = game.total["over"]
    pin_over = game.pinnacle_total["over"]
    if hr_over.handicap is None or pin_over.handicap is None:
        return []
    if abs(hr_over.handicap - pin_over.handicap) > 0.01:
        return []
    line = game.total["over"].handicap
    over_label = f"Over {line}" if line is not None else "Over"
    under_label = f"Under {line}" if line is not None else "Under"

    fair_over, fair_under = _fair_probs_from_pinnacle(
        game.pinnacle_total["over"], game.pinnacle_total["under"]
    )
    picks: list[Pick] = []
    for side_key, label, fair_prob, hr_line in [
        ("over", over_label, fair_over, game.total["over"]),
        ("under", under_label, fair_under, game.total["under"]),
    ]:
        dec = american_to_decimal(hr_line.american)
        edge = edge_pct(fair_prob, dec)
        if edge < min_edge or edge > 20.0:
            continue
        picks.append(
            Pick(
                fixture_id=game.fixture_id,
                sport=game.sport,
                home_team=game.home_team,
                away_team=game.away_team,
                start_time=game.start_time,
                market=MarketType.TOTAL,
                side=Side.OVER if side_key == "over" else Side.UNDER,
                selection=label,
                hard_rock_line=hr_line,
                fair_line=Line(
                    american=_prob_to_american(fair_prob),
                    decimal=1.0 / fair_prob if fair_prob > 0 else 99.0,
                    handicap=hr_line.handicap,
                ),
                edge_pct=round(edge, 2),
                stake_usd=stake,
                confidence=confidence_label(edge),
                hard_rock_url=game.hard_rock_url,
                reason=f"Pinnacle fair prob {fair_prob*100:.1f}% vs Hard Rock {hr_line.american}",
            )
        )
    return picks
