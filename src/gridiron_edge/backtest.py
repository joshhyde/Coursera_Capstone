from __future__ import annotations

from dataclasses import asdict
from typing import Any

from gridiron_edge.models import BacktestResult, MarketType
from gridiron_edge.odds_math import (
    moneyline_covers,
    payout_usd,
    spread_covers,
    total_covers,
)


def run_backtest(
  records: list[dict[str, Any]],
  *,
  stake_usd: float = 5.0,
) -> BacktestResult:
    """Backtest against settled games with known scores.

    Each record needs:
      home_score, away_score, market, side, american_odds,
      handicap (spread/total), sport
    """
    wins = losses = pushes = 0
    profit = 0.0
    by_market: dict[str, dict[str, float]] = {}
    by_sport: dict[str, dict[str, float]] = {}

    for rec in records:
        market = rec["market"]
        side = rec["side"]
        home = int(rec["home_score"])
        away = int(rec["away_score"])
        american = rec["american_odds"]
        sport = rec.get("sport", "unknown")

        if market == MarketType.MONEYLINE.value or market == "moneyline":
            result = moneyline_covers(home, away, side)
        elif market == MarketType.SPREAD.value or market == "spread":
            result = spread_covers(home, away, side, float(rec["handicap"]))
        elif market == MarketType.TOTAL.value or market == "total":
            result = total_covers(home, away, side, float(rec["handicap"]))
        else:
            continue

        pnl = payout_usd(stake_usd, american, result)
        profit += pnl

        if result == "win":
            wins += 1
        elif result == "loss":
            losses += 1
        else:
            pushes += 1

        _bucket(by_market, market, result)
        _bucket(by_sport, sport, result)

    decided = wins + losses
    win_rate = (wins / decided * 100.0) if decided else 0.0
    total_staked = (wins + losses) * stake_usd
    roi = (profit / total_staked * 100.0) if total_staked else 0.0

    return BacktestResult(
        total_bets=wins + losses + pushes,
        wins=wins,
        losses=losses,
        pushes=pushes,
        win_rate=round(win_rate, 1),
        roi_pct=round(roi, 1),
        profit_usd=round(profit, 2),
        by_market=_summarize_buckets(by_market),
        by_sport=_summarize_buckets(by_sport),
    )


def _bucket(store: dict[str, dict[str, float]], key: str, result: str) -> None:
    if key not in store:
        store[key] = {"wins": 0, "losses": 0, "pushes": 0}
    field = {"win": "wins", "loss": "losses", "push": "pushes"}[result]
    store[key][field] += 1


def _summarize_buckets(store: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for key, counts in store.items():
        w = counts.get("wins", 0)
        l = counts.get("losses", 0)
        decided = w + l
        out[key] = {
            "wins": w,
            "losses": l,
            "pushes": counts.get("pushes", 0),
            "win_rate": round(w / decided * 100, 1) if decided else 0.0,
        }
    return out


def backtest_result_to_dict(result: BacktestResult) -> dict[str, Any]:
    return asdict(result)
