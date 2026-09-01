# Gridiron

CLI that ranks Hard Rock Bet prices for NFL and college football against a no-vig fair line from OddsPapi.

This is a recommendation engine. It does not place bets.

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp gridiron/.env.example .env   # set ODDS_API_KEY
```

## Usage

```bash
python -m gridiron picks --league nfl
python -m gridiron picks --league ncaaf --json
python -m gridiron picks --min-ev 0.02
```

Tests that do not call the network:

```bash
pytest
```

A live smoke test (needs `ODDS_API_KEY`):

```bash
python -m gridiron picks --league nfl --limit 3
```

## Data

OddsPapi v4 at `https://api.oddspapi.io/v4`. See `.cursor/rules/gridiron.mdc` for sport IDs, book slugs, and the fair-price rule.
