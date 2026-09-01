from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    oddspapi_api_key: str = ""
    the_odds_api_key: str = ""

    stake_usd: float = 5.0
    min_edge_pct: float = 2.0

    daily_api_budget: int = 6
    cache_ttl_hours: int = 6

    host: str = "0.0.0.0"
    port: int = 8787

    data_dir: Path = Path.home() / ".gridiron-edge"

    nfl_tournament_id: int = 31
    ncaa_tournament_id: int = 850

    target_book: str = "hardrockbet"
    sharp_book: str = "pinnacle"

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, value: str | Path) -> Path:
        return Path(value).expanduser()

    @property
    def db_path(self) -> Path:
        return self.data_dir / "gridiron.db"

    @property
    def api_usage_path(self) -> Path:
        return self.data_dir / "api_usage.json"


def get_settings() -> Settings:
    return Settings()
