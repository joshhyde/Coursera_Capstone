# Gridiron Edge

CFB and NFL +EV pick engine for **Hard Rock Bet** (Florida). Compares Hard Rock lines against Pinnacle (sharp book) and surfaces positive expected value on spreads, moneylines, and totals.

This is its own project. It is not part of the Coursera capstone.

## Strategy (v1)

1. Pull odds from OddsPapi (`hardrockbet` + `pinnacle`)
2. Remove vig from Pinnacle to estimate fair probability
3. Compare Hard Rock implied odds to fair line
4. Surface picks where edge ≥ 2% at $5 flat stake
5. Track win rate and profit over time

## Quick start (Mac mini)

**One command** (installs Python 3.11+ if needed, starts the dashboard on boot, enables LAN access):

```bash
git clone https://github.com/joshhyde/gridiron-edge.git
cd gridiron-edge
chmod +x scripts/setup-mac-mini.sh
ODDSPAPI_API_KEY=your-key-here ./scripts/setup-mac-mini.sh
```

Requires **Python 3.11+**. macOS ships 3.9; the setup script auto-installs `python@3.12` via Homebrew if needed.

Then open:
- **On the Mac mini:** http://127.0.0.1:8787
- **Phone / iPad:** the URL the script prints, e.g. `http://192.168.0.253:8787`

Do **not** open `http://0.0.0.0:8787` or `http://localhost:8787` on the phone — those only work on the Mac. In Safari type `http://` yourself; iOS will try https and fail.

### Manual setup

```bash
chmod +x scripts/install-mac.sh
./scripts/install-mac.sh
nano .env   # add API key, set HOST=0.0.0.0
source .venv/bin/activate
gridiron sync
gridiron serve
```

## Access from other devices

| Where you are | How to connect |
|---|---|
| Same home Wi‑Fi | `http://<mac-mini-local-ip>:8787` (Safari address bar, **http not https**) |
| Away from home / cellular | [Tailscale](https://tailscale.com/download) on Mac mini + phone |
| Public internet | Not configured (use Tailscale instead of port forwarding) |

Print the URLs a phone can actually open:

```bash
.venv/bin/gridiron urls
./scripts/doctor.sh
```

`0.0.0.0` means “listen on every interface on this Mac.” It is **not** a URL. `localhost` on your phone is the phone itself.

Find the Mac mini IP in **System Settings → Network**, or run `ipconfig getifaddr en0`. If it still fails: same Wi‑Fi (not guest), macOS Firewall allow Python, no VPN on the phone.

**Tailscale (access anywhere):** Install on the Mac mini and your phone. Use the Mac mini's Tailscale IP (e.g. `http://100.x.x.x:8787`) from cellular.

## Configuration

Copy `.env.example` to `.env`:

| Variable | Default | Description |
|---|---|---|
| `ODDSPAPI_API_KEY` | — | Your OddsPapi key |
| `STAKE_USD` | 5.00 | Flat bet size |
| `MIN_EDGE_PCT` | 2.0 | Minimum +EV to recommend |
| `DAILY_API_BUDGET` | 4 | Max API calls/day (free tier) |
| `CACHE_TTL_HOURS` | 6 | How long to cache odds |

## API budget (free tier)

OddsPapi free tier is limited (~250 requests/month). Gridiron Edge conserves calls by:

- Batching NFL + NCAA in one `odds-by-tournaments` call
- Caching responses in SQLite for 6 hours
- Default cap of 4 API calls per day
- Serving dashboard from local cache when budget is exhausted

Hard Rock Bet has no public API. OddsPapi is the primary source and includes direct `app.hardrock.bet` links per fixture.

## Dashboard

The web UI shows:

- Win rate and profit tracking
- Today's +EV picks ranked by edge
- One-click links to Hard Rock Bet
- API budget usage
- Demo backtest module

## CLI

```bash
gridiron sync    # Fetch odds, generate picks
gridiron serve   # Start dashboard (prints phone URLs)
gridiron urls    # Print phone/iPad URLs without starting the server
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Disclaimer

This tool is for personal research and entertainment. Sports betting involves risk. Bet responsibly within your means. Gridiron Edge does not place bets automatically.
