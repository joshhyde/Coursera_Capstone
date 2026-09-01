from __future__ import annotations

import logging
from typing import Any

from gridiron_edge.api_client import ApiBudgetExceeded, OddsPapiClient
from gridiron_edge.config import Settings
from gridiron_edge.engine import generate_picks
from gridiron_edge.models import GameOdds, Pick
from gridiron_edge.parser import parse_fixture, sport_for_tournament
from gridiron_edge.storage import Storage

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, settings: Settings, storage: Storage, client: OddsPapiClient) -> None:
        self.settings = settings
        self.storage = storage
        self.client = client

    def ensure_market_meta(self) -> None:
        cached = self.storage.get_cache("market_meta_sport14")
        if cached:
            self.storage.upsert_market_meta(cached)
            return
        markets = self.client.get_markets(sport_id=14)
        self.storage.upsert_market_meta(markets)
        self.storage.set_cache("market_meta_sport14", markets, ttl_hours=168)

    def fetch_slate(self) -> list[GameOdds]:
        self.ensure_market_meta()
        tournament_ids = [self.settings.nfl_tournament_id, self.settings.ncaa_tournament_id]

        try:
            fixtures = self.client.get_odds_by_tournaments_both_books(tournament_ids)
        except ApiBudgetExceeded:
            logger.warning("API budget exceeded — loading fixtures from cache/db")
            fixtures = self._fixtures_from_db()

        games: list[GameOdds] = []
        for raw in fixtures:
            tid = raw.get("tournamentId")
            sport = sport_for_tournament(
                tid, self.settings.nfl_tournament_id, self.settings.ncaa_tournament_id
            )
            if sport == "unknown":
                continue

            fixture_id = raw.get("fixtureId")
            if not fixture_id:
                continue

            if raw.get("bookmakerOdds"):
                game = parse_fixture(raw, sport, self.storage)
            else:
                try:
                    detail = self.client.get_fixture_odds(fixture_id)
                    game = parse_fixture(detail, sport, self.storage)
                except ApiBudgetExceeded:
                    continue

            if game.home_team in ("Home", None) or game.away_team in ("Away", None):
                game = self._enrich_names(game, sport, raw)

            games.append(game)
            self.storage.upsert_fixture(
                {
                    "fixture_id": game.fixture_id,
                    "sport": game.sport,
                    "tournament_id": tid,
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "start_time": game.start_time,
                    "status": raw.get("statusName"),
                    "hard_rock_url": game.hard_rock_url,
                    "raw_json": raw,
                }
            )

        return games

    def _enrich_names(self, game: GameOdds, sport: str, raw: dict[str, Any]) -> GameOdds:
        with self.storage.connect() as conn:
            row = conn.execute(
                "SELECT home_team, away_team FROM fixtures WHERE fixture_id = ?",
                (game.fixture_id,),
            ).fetchone()
        if row and row["home_team"] and row["away_team"]:
            game.home_team = row["home_team"]
            game.away_team = row["away_team"]
            return game

        try:
            detail = self.client.get_fixture_odds(game.fixture_id)
            return parse_fixture(detail, sport, self.storage)
        except ApiBudgetExceeded:
            return game

    def _fixtures_from_db(self) -> list[dict[str, Any]]:
        with self.storage.connect() as conn:
            rows = conn.execute(
                "SELECT raw_json FROM fixtures ORDER BY start_time ASC LIMIT 50"
            ).fetchall()
        import json

        result = []
        for row in rows:
            if row["raw_json"]:
                result.append(json.loads(row["raw_json"]))
        return result

    def run_picks(self) -> list[Pick]:
        games = self.fetch_slate()
        picks = generate_picks(
            games,
            min_edge_pct=self.settings.min_edge_pct,
            stake_usd=self.settings.stake_usd,
        )
        for pick in picks:
            self.storage.save_pick(
                {
                    "fixture_id": pick.fixture_id,
                    "sport": pick.sport,
                    "market": pick.market.value,
                    "side": pick.side.value,
                    "selection": pick.selection,
                    "american_odds": pick.hard_rock_line.american,
                    "edge_pct": pick.edge_pct,
                    "stake_usd": pick.stake_usd,
                    "hard_rock_url": pick.hard_rock_url,
                    "reason": pick.reason,
                }
            )
        return picks
