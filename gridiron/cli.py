from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from gridiron.client import OddsClient, OddsPapiError
from gridiron.constants import ENV_KEY, TOURNAMENTS
from gridiron.models import Pick
from gridiron.parse import parse_quotes
from gridiron.rank import rank_picks

MISSING_KEY = (
    f"{ENV_KEY} is not set. Copy gridiron/.env.example to .env and export the key. "
    "The CLI never reads a committed secret."
)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "picks":
        return _picks(args)
    parser.print_help()
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gridiron",
        description="Rank +EV Hard Rock Bet NFL and NCAAF mainlines. Recommendations only.",
    )
    sub = parser.add_subparsers(dest="command")
    picks = sub.add_parser("picks", help="print ranked Hard Rock +EV mainlines")
    picks.add_argument("--league", required=True, choices=sorted(TOURNAMENTS))
    picks.add_argument("--min-ev", type=float, default=0.0, dest="min_ev")
    picks.add_argument("--json", action="store_true")
    picks.add_argument("--limit", type=int, default=None)
    return parser


def _picks(args: argparse.Namespace) -> int:
    _load_dotenv()
    key = os.environ.get(ENV_KEY, "").strip()
    if not key:
        print(MISSING_KEY, file=sys.stderr)
        return 2
    try:
        client = OddsClient(key)
        catalog = client.fetch_markets()
        payloads = client.fetch_league_odds(args.league)
    except OddsPapiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    quotes = parse_quotes(payloads, catalog)
    picks = rank_picks(quotes, league=args.league, min_ev=args.min_ev)
    if args.limit is not None:
        picks = picks[: max(0, args.limit)]
    if args.json:
        print(json.dumps([p.as_json() for p in picks], indent=2))
        return 0
    print(_table(picks, args.min_ev))
    return 0


def _table(picks: list[Pick], min_ev: float) -> str:
    if not picks:
        return f"No +EV Hard Rock picks above min-ev {min_ev:g}."
    headers = (
        "EV",
        "Kelly/4",
        "Odds",
        "Fair",
        "Market",
        "Selection",
        "Fixture",
        "Start",
        "Books",
        "Note",
    )
    rows = [headers]
    for pick in picks:
        payload = pick.as_json()
        rows.append(
            (
                f"{payload['ev']:+.1%}",
                f"{payload['kelly_quarter']:.1%}",
                _american(payload["american_odds"]),
                f"{payload['fair_prob']:.1%}",
                payload["market"],
                payload["selection"],
                payload["fixture"],
                payload["start_time"],
                ",".join(pick.books_used),
                pick.disagreement or "",
            )
        )
    widths = [max(len(row[i]) for row in rows) for i in range(len(headers))]
    lines = []
    for index, row in enumerate(rows):
        line = "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
        lines.append(line)
        if index == 0:
            lines.append("  ".join("-" * widths[i] for i in range(len(headers))))
    return "\n".join(lines)


def _american(odds: int) -> str:
    return f"+{odds}" if odds > 0 else str(odds)


def _load_dotenv() -> None:
    if os.environ.get(ENV_KEY, "").strip():
        return
    for path in (Path(".env"), Path("gridiron/.env")):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == ENV_KEY and value.strip():
                os.environ[ENV_KEY] = value.strip().strip('"').strip("'")
                return
