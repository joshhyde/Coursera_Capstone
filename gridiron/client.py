from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from gridiron.constants import (
    BOOK_GAP_SEC,
    BOOKS,
    HOST,
    SPORT_ID,
    TOURNAMENTS,
    USER_AGENT,
)

MAX_RETRIES = 5

Opener = Callable[[urllib.request.Request, float], Any]


class OddsPapiError(RuntimeError):
    pass


class OddsClient:
    def __init__(
        self,
        api_key: str,
        *,
        sleep: Callable[[float], None] = time.sleep,
        urlopen: Opener | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self._sleep = sleep
        self._urlopen = urlopen or urllib.request.urlopen
        self._timeout = timeout

    def fetch_markets(self) -> list[dict]:
        body = self._get("markets", sportId=SPORT_ID)
        if not isinstance(body, list):
            raise OddsPapiError("GET /markets did not return a list")
        return body

    def fetch_book_odds(self, tournament_id: int, bookmaker: str) -> list:
        body = self._get(
            "odds-by-tournaments",
            tournamentIds=tournament_id,
            bookmaker=bookmaker,
            verbosity=3,
        )
        if isinstance(body, list):
            return body
        if isinstance(body, dict) and body.get("fixtureId"):
            return [body]
        for key in ("data", "fixtures", "results"):
            rows = body.get(key) if isinstance(body, dict) else None
            if isinstance(rows, list):
                return rows
        raise OddsPapiError(f"GET /odds-by-tournaments returned an unexpected body for {bookmaker}")

    def fetch_league_odds(self, league: str) -> list[list]:
        tournament_id = TOURNAMENTS[league]
        payloads: list[list] = []
        for index, book in enumerate(BOOKS):
            if index:
                self._sleep(BOOK_GAP_SEC)
            payloads.append(self.fetch_book_odds(tournament_id, book))
        return payloads

    def _get(self, path: str, **params: Any) -> Any:
        query = urllib.parse.urlencode(
            {"apiKey": self.api_key, **{k: v for k, v in params.items() if v is not None}}
        )
        url = f"{HOST}/{path}?{query}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        last_error: OddsPapiError | None = None
        for attempt in range(MAX_RETRIES):
            try:
                with self._urlopen(request, timeout=self._timeout) as response:
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace") if exc.fp else ""
                last_error = OddsPapiError(f"OddsPapi {exc.code} on /{path}: {detail[:300]}")
                if exc.code == 429 and attempt < MAX_RETRIES - 1:
                    self._sleep(_retry_wait_sec(detail))
                    continue
                raise last_error from exc
            except urllib.error.URLError as exc:
                raise OddsPapiError(f"OddsPapi request failed on /{path}: {exc.reason}") from exc
            try:
                body = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise OddsPapiError(f"OddsPapi returned non-JSON on /{path}") from exc
            if isinstance(body, dict) and body.get("error"):
                raise OddsPapiError(f"OddsPapi error on /{path}: {body}")
            return body
        raise last_error or OddsPapiError(f"OddsPapi request failed on /{path}")


def _retry_wait_sec(detail: str) -> float:
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return BOOK_GAP_SEC
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return BOOK_GAP_SEC
    ms = error.get("retryMs")
    if isinstance(ms, (int, float)) and ms >= 0:
        return max(BOOK_GAP_SEC, ms / 1000.0)
    return BOOK_GAP_SEC
