from gridiron_edge.config import Settings


def test_ncaaf_uses_regular_season_tournament_not_empty_ncaa_catalog():
    settings = Settings()
    assert settings.nfl_tournament_id == 31
    assert settings.ncaa_tournament_id == 27653
    assert settings.ncaa_tournament_id != 850
