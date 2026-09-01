from gridiron_edge.backtest import run_backtest


def test_backtest_win_rate():
    records = [
        {
            "sport": "nfl",
            "market": "moneyline",
            "side": "home",
            "american_odds": "-150",
            "home_score": 24,
            "away_score": 17,
        },
        {
            "sport": "nfl",
            "market": "moneyline",
            "side": "home",
            "american_odds": "-150",
            "home_score": 10,
            "away_score": 28,
        },
    ]
    result = run_backtest(records, stake_usd=5.0)
    assert result.total_bets == 2
    assert result.wins == 1
    assert result.losses == 1
    assert result.win_rate == 50.0
