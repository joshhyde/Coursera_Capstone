from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Quote:
    book: str
    market_type: str
    period: str
    line: float | None
    side: str
    decimal_odds: float
    american_odds: int
    fixture_id: str
    start_time: str
    home: str
    away: str
    main_line: bool


@dataclass(frozen=True)
class MarketBook:
    fixture_id: str
    market_type: str
    period: str
    line: float | None
    quotes: tuple[Quote, ...]

    def sides(self) -> frozenset[str]:
        return frozenset(q.side for q in self.quotes)

    def by_book(self, book: str) -> dict[str, Quote]:
        return {q.side: q for q in self.quotes if q.book == book}


@dataclass(frozen=True)
class Fair:
    probs: Mapping[str, float]
    source: str
    books_used: tuple[str, ...]


@dataclass(frozen=True)
class Pick:
    quote: Quote
    fair: Fair
    ev: float
    kelly_quarter: float
    books_used: tuple[str, ...]
    disagreement: str | None
    league: str

    @property
    def fixture(self) -> str:
        return f"{self.quote.away} @ {self.quote.home}"

    @property
    def selection(self) -> str:
        q = self.quote
        if q.market_type == "total":
            line = q.line if q.line is not None else ""
            return f"{q.side} {line}".strip()
        if q.market_type == "spread":
            signed = _signed_line(q.line, q.side)
            name = q.home if q.side == "home" else q.away
            return f"{name} {signed}".strip()
        return q.home if q.side == "home" else q.away

    @property
    def selection_line(self) -> float | None:
        q = self.quote
        if q.line is None or q.market_type == "moneyline":
            return None
        if q.market_type == "spread" and q.side == "away":
            return round(-q.line, 3)
        return q.line

    def as_json(self) -> dict:
        q = self.quote
        return {
            "ev": round(self.ev, 6),
            "american_odds": q.american_odds,
            "fair_prob": round(self.fair.probs[q.side], 6),
            "kelly_quarter": round(self.kelly_quarter, 6),
            "fixture": self.fixture,
            "league": self.league,
            "market": q.market_type,
            "selection": self.selection,
            "line": self.selection_line,
            "start_time": q.start_time,
            "home": q.home,
            "away": q.away,
        }


def _signed_line(line: float | None, side: str) -> str:
    if line is None:
        return ""
    value = -line if side == "away" else line
    return f"{value:+g}"
