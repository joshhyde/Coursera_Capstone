from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from gridiron_edge.config import Settings
from gridiron_edge.storage import Storage

logger = logging.getLogger(__name__)

BASE_URL = "https://api.oddspapi.io/v4"
ENDPOINT_COOLDOWN_SEC = 1.0


class ApiBudgetExceeded(Exception):
    pass


class OddsPapiClient:
    def __init__(self, settings: Settings, storage: Storage) -> None:
        self.settings = settings
        self.storage = storage
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def _can_call_api(self) -> bool:
        return self.storage.api_calls_today() < self.settings.daily_api_budget

    def _request(self, path: str, params: dict[str, Any] | None = None, *, use_cache: bool = True) -> Any:
        params = dict(params or {})
        params["apiKey"] = self.settings.oddspapi_api_key
        cache_key = f"{path}?{sorted(params.items())}"

        if use_cache:
            cached = self.storage.get_cache(cache_key)
            if cached is not None:
                logger.debug("cache hit: %s", path)
                return cached

        if not self._can_call_api():
            raise ApiBudgetExceeded(
                f"Daily API budget ({self.settings.daily_api_budget}) exhausted. "
                "Using cached data only until tomorrow."
            )

        url = f"{BASE_URL}{path}"
        resp = self._client.get(url, params=params)
        self.storage.log_api_call(path, resp.status_code)
        if resp.status_code == 429:
            retry = float(resp.json().get("error", {}).get("retryMs", 1000)) / 1000.0
            time.sleep(retry + 0.1)
            resp = self._client.get(url, params=params)
            self.storage.log_api_call(path, resp.status_code)
        resp.raise_for_status()
        data = resp.json()
        time.sleep(ENDPOINT_COOLDOWN_SEC)

        if use_cache:
            self.storage.set_cache(cache_key, data, self.settings.cache_ttl_hours)
        return data

    def get_markets(self, sport_id: int = 14) -> list[dict[str, Any]]:
        return self._request("/markets", {"sportId": sport_id})

    def get_odds_by_tournaments(
        self,
        tournament_ids: list[int],
        bookmaker: str | None = None,
    ) -> list[dict[str, Any]]:
        bookmaker = bookmaker or self.settings.target_book
        return self._request(
            "/odds-by-tournaments",
            {
                "bookmaker": bookmaker,
                "tournamentIds": ",".join(str(t) for t in tournament_ids),
                "oddsFormat": "american",
            },
            use_cache=False,
        )

    def get_odds_by_tournaments_both_books(
        self,
        tournament_ids: list[int],
    ) -> list[dict[str, Any]]:
        """Fetch target + sharp book in two calls and merge by fixture_id."""
        hr_fixtures = self.get_odds_by_tournaments(tournament_ids, self.settings.target_book)
        pin_fixtures = self.get_odds_by_tournaments(tournament_ids, self.settings.sharp_book)
        pin_by_id = {f["fixtureId"]: f for f in pin_fixtures if f.get("fixtureId")}

        merged: list[dict[str, Any]] = []
        for hr in hr_fixtures:
            fid = hr.get("fixtureId")
            if not fid:
                continue
            combined = dict(hr)
            pin = pin_by_id.get(fid)
            if pin and pin.get("bookmakerOdds"):
                hr_odds = combined.setdefault("bookmakerOdds", {})
                hr_odds.update(pin.get("bookmakerOdds", {}))
            merged.append(combined)
        return merged

    def get_fixture_odds(self, fixture_id: str, bookmakers: str | None = None) -> dict[str, Any]:
        bookmakers = bookmakers or f"{self.settings.target_book},{self.settings.sharp_book}"
        return self._request(
            "/odds",
            {
                "fixtureId": fixture_id,
                "bookmakers": bookmakers,
                "verbosity": 3,
                "oddsFormat": "american",
            },
        )

    def get_historical_odds(self, fixture_id: str) -> dict[str, Any]:
        return self._request(
            "/historical-odds",
            {
                "fixtureId": fixture_id,
                "bookmakers": f"{self.settings.target_book},{self.settings.sharp_book}",
            },
            use_cache=False,
        )
