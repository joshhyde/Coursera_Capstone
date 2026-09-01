from gridiron_edge.odds_math import (
    american_to_decimal,
    american_to_implied_prob,
    edge_pct,
    moneyline_covers,
    payout_usd,
    remove_vig,
    spread_covers,
    total_covers,
)


def test_american_to_decimal_favorites():
    assert abs(american_to_decimal("-150") - 1.667) < 0.01
    assert american_to_decimal("+150") == 2.5


def test_remove_vig():
    fair_a, fair_b = remove_vig(0.55, 0.55)
    assert abs(fair_a - 0.5) < 0.001
    assert abs(fair_b - 0.5) < 0.001


def test_edge_positive_when_fair_above_implied():
    fair_prob = 0.55
    decimal = 2.0
    assert edge_pct(fair_prob, decimal) > 0


def test_spread_covers():
    assert spread_covers(24, 20, "home", -3.5) == "win"
    assert spread_covers(24, 20, "away", -3.5) == "loss"


def test_total_covers():
    assert total_covers(28, 24, "over", 50.5) == "win"
    assert total_covers(28, 24, "under", 50.5) == "loss"


def test_moneyline_covers():
    assert moneyline_covers(21, 14, "home") == "win"
    assert moneyline_covers(21, 14, "away") == "loss"


def test_payout():
    assert payout_usd(5.0, "+100", "win") == 5.0
    assert payout_usd(5.0, "-110", "loss") == -5.0
    assert payout_usd(5.0, "-110", "push") == 0.0
