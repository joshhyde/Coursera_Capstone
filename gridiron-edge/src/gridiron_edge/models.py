from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class MarketType(str, Enum):
    MONEYLINE = "moneyline"
    SPREAD = "spread"
    TOTAL = "total"


class Side(str, Enum):
    HOME = "home"
    AWAY = "away"
    OVER = "over"
    UNDER = "under"


@dataclass(frozen=True)
class Line:
    american: str
    decimal: float
    handicap: float | None = None


@dataclass
class GameOdds:
    fixture_id: str
    sport: Literal["nfl", "cfb"]
    home_team: str
    away_team: str
    start_time: str
    hard_rock_url: str | None
    moneyline: dict[str, Line] | None = None
    spread: dict[str, Line] | None = None
    total: dict[str, Line] | None = None
    pinnacle_moneyline: dict[str, Line] | None = None
    pinnacle_spread: dict[str, Line] | None = None
    pinnacle_total: dict[str, Line] | None = None


@dataclass
class Pick:
    fixture_id: str
    sport: str
    home_team: str
    away_team: str
    start_time: str
    market: MarketType
    side: Side
    selection: str
    hard_rock_line: Line
    fair_line: Line
    edge_pct: float
    stake_usd: float
    confidence: str
    hard_rock_url: str | None
    reason: str


@dataclass
class BacktestResult:
    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    roi_pct: float
    profit_usd: float
    by_market: dict[str, dict[str, float]]
    by_sport: dict[str, dict[str, float]]
