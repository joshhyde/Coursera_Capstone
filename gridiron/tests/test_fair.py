import pytest

from gridiron.fair import expected_value, kelly_quarter, multiplicative_devig


def test_multiplicative_devig_even_book():
    probs = multiplicative_devig({"home": 1.91, "away": 1.91})
    assert probs["home"] == pytest.approx(0.5)
    assert probs["away"] == pytest.approx(0.5)
    assert abs(sum(probs.values()) - 1) < 1e-12


def test_multiplicative_devig_strips_overround():
    probs = multiplicative_devig({"home": 1.5, "away": 2.6})
    assert abs(sum(probs.values()) - 1) < 1e-12
    implied = 1 / 1.5 + 1 / 2.6
    assert probs["home"] == pytest.approx((1 / 1.5) / implied)


def test_ev_and_quarter_kelly_on_plus_ev_price():
    ev = expected_value(0.5, 2.2)
    assert ev == pytest.approx(0.1)
    b = 1.2
    full = (b * 0.5 - 0.5) / b
    assert kelly_quarter(0.5, 2.2) == pytest.approx(full / 4)


def test_kelly_zero_when_price_is_minus_ev():
    assert kelly_quarter(0.4, 1.5) == 0.0
