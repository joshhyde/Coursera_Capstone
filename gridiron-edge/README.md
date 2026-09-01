# Gridiron Edge

CFB and NFL +EV pick engine built for **Hard Rock Bet** (Florida). Compares Hard Rock lines against Pinnacle (sharp book) to find positive expected value bets on spreads, moneylines, and totals.

## Strategy (v1)

1. Pull odds from OddsPapi (`hardrockbet` + `pinnacle`)
2. Remove vig from Pinnacle to estimate fair probability
3. Compare Hard Rock implied odds to fair line
4. Surface picks where edge ≥ 2% at $5 flat stake
5. Track win rate and profit over time

Future: evolve to hybrid statistical model (Option C).

## Quick start (Mac mini)

```bash
git clone https://github.com/joshhyde/gridiron-edge.git
cd gridiron-edge
chmod +x scripts/install-mac.sh
./scripts/install-mac.sh

# Add your API key
nano .env

# Generate picks
source .venv/bin/activate
gridiron sync

# Launch dashboard
gridiron serve
# Open http://127.0.0.1:8787
```

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

## Scheduled sync (optional)

```bash
# Edit paths in scripts/com.gridiron-edge.sync.plist first
cp scripts/com.gridiron-edge.sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.gridiron-edge.sync.plist
```

Runs sync at 8 AM and 4 PM ET.

## CLI

```bash
gridiron sync    # Fetch odds, generate picks
gridiron serve   # Start dashboard
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap (autopilot-stack)

| PR | Scope |
|---|---|
| 1 | Core engine + dashboard (this PR) |
| 2 | Historical backtest with OddsPapi settlement data |
| 3 | Pick result grading (auto-settle from scores) |
| 4 | Team stats enrichment (EPA, SP+, weather) |
| 5 | Hybrid model overlay |

## Disclaimer

This tool is for personal research and entertainment. Sports betting involves risk. Bet responsibly within your means. Gridiron Edge does not place bets automatically.
