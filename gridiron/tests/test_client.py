import json
from urllib.request import Request

from gridiron.client import OddsClient
from gridiron.constants import HOST, USER_AGENT


class _Resp:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def test_odds_call_uses_v4_query_api_key_user_agent_and_singular_bookmaker():
    seen: dict = {}

    def fake_open(request: Request, timeout=None):
        seen["url"] = request.full_url
        seen["ua"] = request.get_header("User-agent")
        seen["auth"] = request.get_header("Authorization")
        seen["timeout"] = timeout
        return _Resp(b"[]")

    client = OddsClient("secret-test-key", urlopen=fake_open, sleep=lambda _: None)
    client.fetch_book_odds(31, "hardrockbet")
    url = seen["url"]
    assert url.startswith(f"{HOST}/odds-by-tournaments?")
    assert "apiKey=secret-test-key" in url
    assert "bookmaker=hardrockbet" in url
    assert "bookmakers=" not in url
    assert "verbosity=3" in url
    assert seen["ua"] == USER_AGENT
    assert seen["auth"] is None


def test_league_fetch_sleeps_between_books():
    sleeps: list[float] = []
    calls: list[str] = []

    def fake_open(request: Request, timeout=None):
        calls.append(request.full_url)
        return _Resp(b"[]")

    client = OddsClient("k", urlopen=fake_open, sleep=sleeps.append)
    client.fetch_league_odds("nfl")
    assert len(calls) == 6
    assert sleeps == [1.0, 1.0, 1.0, 1.0, 1.0]
    assert all("v5." not in url for url in calls)
    assert all("bookmaker=" in url for url in calls)
    assert "tournamentIds=31" in calls[0]


def test_ncaaf_uses_regular_season_tournament():
    calls: list[str] = []

    def fake_open(request: Request, timeout=None):
        calls.append(request.full_url)
        return _Resp(b"[]")

    client = OddsClient("k", urlopen=fake_open, sleep=lambda _: None)
    client.fetch_league_odds("ncaaf")
    assert "tournamentIds=27653" in calls[0]
    assert "sportId=" not in calls[0]
