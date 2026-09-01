1. Coordinator never authors or edits product code in `gridiron/`. Workers own exclusive branches `cursor/<name>-ce57`.
2. Never commit secrets. OddsPapi key lives in `ODDS_API_KEY` only.
3. Recommendations only. No bet placement, no Hard Rock scraping, no account automation.
4. OddsPapi v4 only. Query param `apiKey`, User-Agent required, one `bookmaker` per `/odds-by-tournaments` call, >=1s between book fetches.
5. Target book `hardrockbet`. Fair line from `pinnacle` when both sides exist, else multiplicative-devig consensus of `circasports,draftkings,fanduel,betmgm`.
6. v1 markets: full-game moneyline, spread, total. Main lines only.
7. Workers never rebase, never force-push, never run `gt`.
8. Verify with pytest on fixtures plus one live `python -m gridiron picks --league nfl` when the key is present.
9. Leave Coursera notebooks and PDFs untouched.
10. `subagent_type` is `generalPurpose` here. `poteto-agent` is not registered. Read `.cursor/plugins/pstack/skills/poteto-mode/SKILL.md` before work.
11. Task model slugs: `cursor-grok-4.6-high-fast` for feature code, `gpt-5.6-sol-xhigh` for specified sequences, `claude-fable-5-thinking-xhigh` for judgment. Do not use pstack default names that are missing from this environment.
12. Open PRs ready (`draft: false`). Conventional Commits titles.
13. Mid-run discoveries that do not block the frontier park as follow-ups.
