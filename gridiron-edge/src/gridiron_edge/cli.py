from __future__ import annotations

import argparse
import logging
import sys

import uvicorn

from gridiron_edge.api_client import ApiBudgetExceeded, OddsPapiClient, RateLimitExceeded
from gridiron_edge.config import get_settings
from gridiron_edge.lan import bind_reaches_lan, phone_urls
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
        if not picks:
            print("No +EV picks right now (Hard Rock lines may be worse than Pinnacle).")
        return 0
    except RateLimitExceeded as exc:
        print(f"Sync skipped: {exc}")
        return 0
    except ApiBudgetExceeded as exc:
        print(f"Sync skipped: {exc}")
        return 0
    finally:
        client.close()


def cmd_serve() -> int:
    settings = get_settings()
    urls = phone_urls(settings.port)
    print(f"Dashboard listening on {settings.host}:{settings.port}")
    print(f"This Mac:        http://127.0.0.1:{settings.port}")
    if not bind_reaches_lan(settings.host):
        print("WARNING: HOST is loopback. Phones cannot connect.")
        print("         Set HOST=0.0.0.0 in .env and restart.")
    elif urls:
        print("Phone / iPad (same Wi-Fi, Safari address bar, http not https):")
        for url in urls:
            print(f"  {url}")
    else:
        print("Phone / iPad:    http://<this-mac-lan-ip>:8787")
        print("                 (System Settings → Network, or: ipconfig getifaddr en0)")
    print("Do not open http://0.0.0.0:8787 or http://localhost:8787 on a phone.")
    print("Those only work on this Mac. Cellular needs Tailscale.")
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    return 0


def cmd_urls() -> int:
    settings = get_settings()
    print(f"http://127.0.0.1:{settings.port}")
    for url in phone_urls(settings.port):
        print(url)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Gridiron Edge CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="Fetch odds and generate picks")
    sub.add_parser("serve", help="Start the web dashboard")
    sub.add_parser("urls", help="Print phone/iPad URLs for the dashboard")

    args = parser.parse_args()
    if args.command == "sync":
        sys.exit(cmd_sync())
    if args.command == "serve":
        sys.exit(cmd_serve())
    if args.command == "urls":
        sys.exit(cmd_urls())
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
