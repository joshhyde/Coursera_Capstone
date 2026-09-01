HOST = "https://api.oddspapi.io/v4"
USER_AGENT = "GridironPicks/0.1"
SPORT_ID = 14
TOURNAMENTS = {"nfl": 31, "ncaaf": 27653}
TARGET_BOOK = "hardrockbet"
SHARP_BOOK = "pinnacle"
FALLBACK_BOOKS = ("circasports", "draftkings", "fanduel", "betmgm")
BOOKS = (TARGET_BOOK, SHARP_BOOK, *FALLBACK_BOOKS)
ENV_KEY = "ODDS_API_KEY"
FULL_GAME_MARKET_NAMES = {
    "Winner (incl. overtime)": "moneyline",
    "Handicap (incl. overtime)": "spread",
    "Total (incl. overtime)": "total",
}
FULL_GAME_PERIODS = {"result", "fulltime", "ft", "full-game", "fullgame"}
MONEYLINE_TYPES = {"moneyline", "ml", "winner"}
SPREAD_TYPES = {"spreads", "spread", "handicap"}
TOTAL_TYPES = {"totals", "total"}
DISAGREE_PP = 0.03
BOOK_GAP_SEC = 1.0
JSON_PICK_KEYS = (
    "ev",
    "american_odds",
    "fair_prob",
    "kelly_quarter",
    "fixture",
    "league",
    "market",
    "selection",
    "line",
    "start_time",
    "home",
    "away",
)
