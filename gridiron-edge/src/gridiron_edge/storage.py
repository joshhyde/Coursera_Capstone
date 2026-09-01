from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    called_at TEXT NOT NULL,
    status_code INTEGER
);

CREATE TABLE IF NOT EXISTS odds_cache (
    cache_key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fixtures (
    fixture_id TEXT PRIMARY KEY,
    sport TEXT NOT NULL,
    tournament_id INTEGER,
    home_team TEXT,
    away_team TEXT,
    start_time TEXT,
    status TEXT,
    home_score INTEGER,
    away_score INTEGER,
    hard_rock_url TEXT,
    raw_json TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS picks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    fixture_id TEXT NOT NULL,
    sport TEXT NOT NULL,
    market TEXT NOT NULL,
    side TEXT NOT NULL,
    selection TEXT NOT NULL,
    american_odds TEXT NOT NULL,
    edge_pct REAL NOT NULL,
    stake_usd REAL NOT NULL,
    result TEXT,
    profit_usd REAL,
    hard_rock_url TEXT,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS market_meta (
    market_id INTEGER PRIMARY KEY,
    market_type TEXT,
    market_name TEXT,
    handicap REAL,
    sport_id INTEGER,
    outcomes_json TEXT
);
"""


class Storage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def log_api_call(self, endpoint: str, status_code: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO api_calls (endpoint, called_at, status_code) VALUES (?, ?, ?)",
                (endpoint, now, status_code),
            )

    def api_calls_today(self) -> int:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM api_calls WHERE called_at LIKE ?",
                (f"{today}%",),
            ).fetchone()
            return int(row["c"])

    def get_cache(self, key: str, *, allow_stale: bool = False) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            if allow_stale:
                row = conn.execute(
                    "SELECT payload FROM odds_cache WHERE cache_key = ?",
                    (key,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT payload FROM odds_cache WHERE cache_key = ? AND expires_at > ?",
                    (key, now),
                ).fetchone()
            if not row:
                return None
            return json.loads(row["payload"])

    def set_cache(self, key: str, payload: dict[str, Any] | list[Any], ttl_hours: int) -> None:
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO odds_cache (cache_key, payload, fetched_at, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload = excluded.payload,
                    fetched_at = excluded.fetched_at,
                    expires_at = excluded.expires_at
                """,
                (key, json.dumps(payload), now.isoformat(), expires.isoformat()),
            )

    def upsert_fixture(self, fixture: dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO fixtures (
                    fixture_id, sport, tournament_id, home_team, away_team,
                    start_time, status, home_score, away_score, hard_rock_url, raw_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fixture_id) DO UPDATE SET
                    sport = excluded.sport,
                    tournament_id = excluded.tournament_id,
                    home_team = excluded.home_team,
                    away_team = excluded.away_team,
                    start_time = excluded.start_time,
                    status = excluded.status,
                    home_score = excluded.home_score,
                    away_score = excluded.away_score,
                    hard_rock_url = excluded.hard_rock_url,
                    raw_json = excluded.raw_json,
                    updated_at = excluded.updated_at
                """,
                (
                    fixture["fixture_id"],
                    fixture["sport"],
                    fixture.get("tournament_id"),
                    fixture.get("home_team"),
                    fixture.get("away_team"),
                    fixture.get("start_time"),
                    fixture.get("status"),
                    fixture.get("home_score"),
                    fixture.get("away_score"),
                    fixture.get("hard_rock_url"),
                    json.dumps(fixture.get("raw_json")),
                    now,
                ),
            )

    def save_pick(self, pick: dict[str, Any]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO picks (
                    created_at, fixture_id, sport, market, side, selection,
                    american_odds, edge_pct, stake_usd, hard_rock_url, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    pick["fixture_id"],
                    pick["sport"],
                    pick["market"],
                    pick["side"],
                    pick["selection"],
                    pick["american_odds"],
                    pick["edge_pct"],
                    pick["stake_usd"],
                    pick.get("hard_rock_url"),
                    pick.get("reason"),
                ),
            )
            return int(cur.lastrowid)

    def list_picks(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM picks ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_pick_result(self, pick_id: int, result: str, profit_usd: float) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE picks SET result = ?, profit_usd = ? WHERE id = ?",
                (result, profit_usd, pick_id),
            )

    def pick_stats(self) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses,
                    SUM(CASE WHEN result = 'push' THEN 1 ELSE 0 END) AS pushes,
                    SUM(COALESCE(profit_usd, 0)) AS profit
                FROM picks WHERE result IS NOT NULL
                """
            ).fetchone()
            total = int(row["total"] or 0)
            wins = int(row["wins"] or 0)
            losses = int(row["losses"] or 0)
            decided = wins + losses
            win_rate = (wins / decided * 100.0) if decided else 0.0
            return {
                "total": total,
                "wins": wins,
                "losses": losses,
                "pushes": int(row["pushes"] or 0),
                "win_rate": round(win_rate, 1),
                "profit_usd": round(float(row["profit"] or 0), 2),
            }

    def upsert_market_meta(self, markets: list[dict[str, Any]]) -> None:
        import json

        with self.connect() as conn:
            for m in markets:
                conn.execute(
                    """
                    INSERT INTO market_meta (market_id, market_type, market_name, handicap, sport_id, outcomes_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(market_id) DO UPDATE SET
                        market_type = excluded.market_type,
                        market_name = excluded.market_name,
                        handicap = excluded.handicap,
                        sport_id = excluded.sport_id,
                        outcomes_json = excluded.outcomes_json
                    """,
                    (
                        m.get("marketId"),
                        m.get("marketType"),
                        m.get("marketName"),
                        m.get("handicap"),
                        m.get("sportId"),
                        json.dumps(m.get("outcomes", [])),
                    ),
                )

    def market_type(self, market_id: int) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT market_type, market_name FROM market_meta WHERE market_id = ?",
                (market_id,),
            ).fetchone()
            if not row:
                return None
            mt = row["market_type"]
            name = (row["market_name"] or "").lower()
            if mt == "moneyline":
                return "moneyline"
            if mt == "spreads" and "overtime" in name:
                return "spread"
            if mt == "totals" and "total (incl. overtime)" == name:
                return "total"
            return None

    def market_outcomes(self, market_id: int) -> dict[str, str]:
        """Map outcome_id -> role (home/away/over/under)."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT market_type, market_name, outcomes_json FROM market_meta WHERE market_id = ?",
                (market_id,),
            ).fetchone()
        if not row:
            return {}
        import json

        outcomes = json.loads(row["outcomes_json"]) if row["outcomes_json"] else []
        mtype = row["market_type"]
        mapping: dict[str, str] = {}
        for o in outcomes:
            oid = str(o.get("outcomeId"))
            name = (o.get("outcomeName") or "").lower()
            if mtype == "moneyline" or mtype == "spreads":
                if name in ("1", "home"):
                    mapping[oid] = "home"
                elif name in ("2", "away"):
                    mapping[oid] = "away"
            elif mtype == "totals":
                if "over" in name:
                    mapping[oid] = "over"
                elif "under" in name:
                    mapping[oid] = "under"
        return mapping
