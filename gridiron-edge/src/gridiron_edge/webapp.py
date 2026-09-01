from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from gridiron_edge.api_client import OddsPapiClient
from gridiron_edge.backtest import backtest_result_to_dict, run_backtest
from gridiron_edge.config import Settings, get_settings
from gridiron_edge.storage import Storage
from gridiron_edge.sync import SyncService

logger = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    storage = Storage(settings.db_path)
    client = OddsPapiClient(settings, storage)
    sync = SyncService(settings, storage, client)

    app = FastAPI(title="Gridiron Edge", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    @app.on_event("shutdown")
    def _shutdown() -> None:
        client.close()

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> HTMLResponse:
        picks = storage.list_picks(limit=50)
        stats = storage.pick_stats()
        api_calls_today = storage.api_calls_today()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "picks": picks,
                "stats": stats,
                "api_calls_today": api_calls_today,
                "api_budget": settings.daily_api_budget,
                "stake_usd": settings.stake_usd,
                "min_edge_pct": settings.min_edge_pct,
            },
        )

    @app.get("/api/status")
    def api_status() -> dict[str, Any]:
        return {
            "api_calls_today": storage.api_calls_today(),
            "api_budget": settings.daily_api_budget,
            "stats": storage.pick_stats(),
        }

    @app.get("/api/picks")
    def api_picks() -> list[dict[str, Any]]:
        return storage.list_picks()

    @app.post("/api/sync")
    def api_sync() -> dict[str, Any]:
        try:
            picks = sync.run_picks()
            return {
                "ok": True,
                "pick_count": len(picks),
                "picks": [_pick_to_dict(p) for p in picks[:20]],
            }
        except Exception as exc:
            logger.exception("sync failed")
            return {"ok": False, "error": str(exc)}

    @app.get("/api/backtest/demo")
    def api_backtest_demo() -> dict[str, Any]:
        """Demo backtest with synthetic settled games to validate the module."""
        demo_records = [
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
                "market": "spread",
                "side": "away",
                "american_odds": "-110",
                "handicap": 3.5,
                "home_score": 21,
                "away_score": 20,
            },
            {
                "sport": "cfb",
                "market": "total",
                "side": "over",
                "american_odds": "-105",
                "handicap": 52.5,
                "home_score": 28,
                "away_score": 31,
            },
            {
                "sport": "cfb",
                "market": "moneyline",
                "side": "away",
                "american_odds": "+120",
                "home_score": 14,
                "away_score": 21,
            },
        ]
        result = run_backtest(demo_records, stake_usd=settings.stake_usd)
        return backtest_result_to_dict(result)

    return app


def _pick_to_dict(pick: Any) -> dict[str, Any]:
    return {
        "fixture_id": pick.fixture_id,
        "sport": pick.sport,
        "home_team": pick.home_team,
        "away_team": pick.away_team,
        "selection": pick.selection,
        "market": pick.market.value,
        "side": pick.side.value,
        "american_odds": pick.hard_rock_line.american,
        "edge_pct": pick.edge_pct,
        "stake_usd": pick.stake_usd,
        "confidence": pick.confidence,
        "hard_rock_url": pick.hard_rock_url,
        "reason": pick.reason,
    }
