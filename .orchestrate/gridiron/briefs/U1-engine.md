GOAL         Ship a Python CLI in gridiron/ that ranks +EV Hard Rock Bet NFL and NCAAF main-line bets from OddsPapi v4.

SCOPE        May write: gridiron/**, tests under gridiron/, pyproject.toml at gridiron/ or repo root if needed, .gitignore entries for .venv/.env. May not write: notebooks, PDFs, .cursor/plugins/pstack.

CONTEXT      Product rules: .cursor/rules/gridiron.mdc and gridiron/README.md. OddsPapi host https://api.oddspapi.io/v4. Sport 14. NFL tournament 31. NCAAF tournament 27653. Book slug hardrockbet. /odds-by-tournaments takes exactly one bookmaker. User-Agent required. verbosity>=3 for team names.

ACCEPTANCE   pytest passes without network.
ACCEPTANCE   `python -m gridiron picks --league nfl` prints a ranked table when ODDS_API_KEY is set, or exits with a clear missing-key error when it is not.
ACCEPTANCE   `--json` emits a list of picks with ev, american_odds, fair_prob, kelly_quarter, fixture, market, selection.
ACCEPTANCE   Key is never written to the repo.
ACCEPTANCE   Coursera notebooks unchanged.

VERIFY       pytest -q
VERIFY       python -m gridiron picks --league nfl --limit 3   (live, if key present)
VERIFY       grep -R the API key string must not match tracked files

TIMEBOX      one cloud agent session

FORBIDDEN    no gt, no rebase, no force-push, no fixes outside scope, no bet placement, no v5 OddsPapi host, no committing .env

REPORT       status, branch, head SHA, PRs, verdict, what you actually ran, deviations, suggested follow-ups
