from __future__ import annotations

from collections import defaultdict

from gridiron.constants import TARGET_BOOK
from gridiron.fair import (
    disagreement_note,
    expected_value,
    fair_price,
    group_books,
    kelly_quarter,
)
from gridiron.models import Pick, Quote


def rank_picks(
    quotes: list[Quote],
    *,
    league: str,
    min_ev: float = 0.0,
    target_book: str = TARGET_BOOK,
) -> list[Pick]:
    mains = _main_line_quotes(quotes, target_book)
    picks: list[Pick] = []
    for market in group_books(mains):
        fair = fair_price(market)
        if fair is None:
            continue
        for quote in market.quotes:
            if quote.book != target_book:
                continue
            prob = fair.probs.get(quote.side)
            if prob is None:
                continue
            ev = expected_value(prob, quote.decimal_odds)
            if ev <= min_ev:
                continue
            picks.append(
                Pick(
                    quote=quote,
                    fair=fair,
                    ev=ev,
                    kelly_quarter=kelly_quarter(prob, quote.decimal_odds),
                    books_used=fair.books_used,
                    disagreement=disagreement_note(market, quote.side),
                    league=league,
                )
            )
    picks.sort(key=lambda p: (-p.ev, p.quote.start_time, p.quote.fixture_id))
    return picks


def _main_line_quotes(quotes: list[Quote], target_book: str) -> list[Quote]:
    groups: dict[tuple[str, str, str], list[Quote]] = defaultdict(list)
    for quote in quotes:
        groups[(quote.fixture_id, quote.market_type, quote.period)].append(quote)
    kept: list[Quote] = []
    for rows in groups.values():
        line = _chosen_line(rows, target_book)
        kept.extend(q for q in rows if _same_line(q.line, line))
    return kept


def _chosen_line(rows: list[Quote], target_book: str) -> float | None:
    target_main = [q.line for q in rows if q.book == target_book and q.main_line]
    if target_main:
        return target_main[0]
    counts: dict[float | None, set[str]] = defaultdict(set)
    for quote in rows:
        counts[quote.line].add(quote.book)
    if not counts:
        return None
    return max(counts, key=lambda line: (len(counts[line]), _line_sort(line)))


def _line_sort(line: float | None) -> float:
    if line is None:
        return 0.0
    return -abs(line)


def _same_line(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return round(left, 3) == round(right, 3)
