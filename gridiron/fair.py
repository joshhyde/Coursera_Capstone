from __future__ import annotations

from collections import defaultdict

from gridiron.constants import DISAGREE_PP, FALLBACK_BOOKS, SHARP_BOOK
from gridiron.models import Fair, MarketBook


def multiplicative_devig(odds: dict[str, float]) -> dict[str, float]:
    implied: dict[str, float] = {}
    for side, price in odds.items():
        if price <= 1:
            continue
        implied[side] = 1.0 / price
    total = sum(implied.values())
    if total <= 0:
        return {}
    return {side: prob / total for side, prob in implied.items()}


def book_two_way(market: MarketBook, book: str) -> dict[str, float] | None:
    needed = market.sides()
    if len(needed) < 2:
        return None
    prices = {q.side: q.decimal_odds for q in market.quotes if q.book == book}
    if not needed.issubset(prices):
        return None
    return {side: prices[side] for side in needed}


def fair_price(market: MarketBook) -> Fair | None:
    pin = book_two_way(market, SHARP_BOOK)
    if pin is not None:
        probs = multiplicative_devig(pin)
        if probs:
            return Fair(probs=probs, source="pinnacle", books_used=(SHARP_BOOK,))
    book_probs: dict[str, dict[str, float]] = {}
    for book in FALLBACK_BOOKS:
        prices = book_two_way(market, book)
        if prices is None:
            continue
        probs = multiplicative_devig(prices)
        if probs:
            book_probs[book] = probs
    if not book_probs:
        return None
    sides = next(iter(book_probs.values())).keys()
    averaged = {}
    for side in sides:
        averaged[side] = sum(p[side] for p in book_probs.values()) / len(book_probs)
    total = sum(averaged.values())
    if total <= 0:
        return None
    renormalized = {side: value / total for side, value in averaged.items()}
    return Fair(
        probs=renormalized,
        source="consensus",
        books_used=tuple(book_probs.keys()),
    )


def disagreement_note(market: MarketBook, side: str) -> str | None:
    samples: dict[str, float] = {}
    for book in (SHARP_BOOK, *FALLBACK_BOOKS):
        prices = book_two_way(market, book)
        if prices is None:
            continue
        probs = multiplicative_devig(prices)
        if side in probs:
            samples[book] = probs[side]
    if len(samples) < 2:
        return None
    spread = max(samples.values()) - min(samples.values())
    if spread < DISAGREE_PP:
        return None
    books = ", ".join(samples)
    return f"no-vig {side} differs by {spread:.1%} across {books}"


def expected_value(fair_prob: float, decimal_odds: float) -> float:
    return fair_prob * decimal_odds - 1.0


def kelly_quarter(fair_prob: float, decimal_odds: float) -> float:
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - fair_prob
    full = (b * fair_prob - q) / b
    return max(0.0, full / 4.0)


def group_books(quotes) -> list[MarketBook]:
    buckets: dict[tuple, list] = defaultdict(list)
    for quote in quotes:
        line = None if quote.line is None else round(quote.line, 3)
        key = (quote.fixture_id, quote.market_type, quote.period, line)
        buckets[key].append(quote)
    books = []
    for (fixture_id, market_type, period, line), rows in buckets.items():
        books.append(
            MarketBook(
                fixture_id=fixture_id,
                market_type=market_type,
                period=period,
                line=line,
                quotes=tuple(rows),
            )
        )
    return books
