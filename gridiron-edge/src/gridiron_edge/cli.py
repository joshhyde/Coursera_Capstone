from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

from gridiron_edge.api_client import OddsPapiClient
from gridiron_edge.config import get_settings
from gridiron_edge.storage import Storage
from gridiron_edge.sync import SyncService
from gridiron_edge.webapp import create_app

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def cmd_sync() -> int:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    storage = Storage(settings.db_path)
    client = OddsPapiClient(settings, storage)
    sync = SyncService(settings, storage, client)
    try:
        picks = sync.run_picks()
        print(f"Generated {len(picks)} +EV picks")
        for p in picks[:10]:
            print(f"  [{p.sport.upper()}] {p.selection} @ {p.hard_rock_line.american} ({p.edge_pct}% edge)")
        return 0
    finally:
        client.close()


def cmd_serve() -> int:
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Gridiron Edge CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="Fetch odds and generate picks")
    sub.add_parser("serve", help="Start the web dashboard")

    args = parser.parse_args()
    if args.command == "sync":
        sys.exit(cmd_sync())
    if args.command == "serve":
        sys.exit(cmd_serve())
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
