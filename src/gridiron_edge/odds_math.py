from __future__ import annotations

import math


def american_to_decimal(american: str | int) -> float:
    s = str(american).strip()
    if s.startswith("+"):
        return 1.0 + int(s[1:]) / 100.0
    if s.startswith("-"):
        return 1.0 + 100.0 / abs(int(s))
    value = int(s)
    if value > 0:
        return 1.0 + value / 100.0
    return 1.0 + 100.0 / abs(value)


def american_to_implied_prob(american: str | int) -> float:
    s = str(american).strip()
    if s.startswith("+"):
        odds = int(s[1:])
        return 100.0 / (odds + 100.0)
    if s.startswith("-"):
        odds = abs(int(s))
        return odds / (odds + 100.0)
    value = int(s)
    if value > 0:
        return 100.0 / (value + 100.0)
    return abs(value) / (abs(value) + 100.0)


def remove_vig(prob_a: float, prob_b: float) -> tuple[float, float]:
    total = prob_a + prob_b
    if total <= 0:
        return 0.5, 0.5
    return prob_a / total, prob_b / total


def edge_pct(fair_prob: float, offered_decimal: float) -> float:
    """Expected value edge as percentage of stake."""
    return (fair_prob * offered_decimal - 1.0) * 100.0


def confidence_label(edge: float) -> str:
    if edge >= 5.0:
        return "high"
    if edge >= 3.0:
        return "medium"
    return "low"


def spread_covers(home_score: int, away_score: int, side: str, handicap: float) -> str:
    """Return win/loss/push for a spread bet. Handicap is from home perspective."""
    margin = home_score - away_score
    adjusted = margin + handicap
    if side == "home":
        if adjusted > 0:
            return "win"
        if adjusted < 0:
            return "loss"
        return "push"
    if adjusted < 0:
        return "win"
    if adjusted > 0:
        return "loss"
    return "push"


def total_covers(home_score: int, away_score: int, side: str, line: float) -> str:
    total = home_score + away_score
    if side == "over":
        if total > line:
            return "win"
        if total < line:
            return "loss"
        return "push"
    if total < line:
        return "win"
    if total > line:
        return "loss"
    return "push"


def moneyline_covers(home_score: int, away_score: int, side: str) -> str:
    if home_score == away_score:
        return "push"
    home_wins = home_score > away_score
    if side == "home":
        return "win" if home_wins else "loss"
    return "win" if not home_wins else "loss"


def payout_usd(stake: float, american: str, result: str) -> float:
    if result == "push":
        return 0.0
    if result == "loss":
        return -stake
    dec = american_to_decimal(american)
    return stake * (dec - 1.0)
