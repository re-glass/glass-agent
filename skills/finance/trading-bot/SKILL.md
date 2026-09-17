---
name: trading-bot
description: A complete production-ready trading bot framework with unified OOP design, 3 strategies, position persistence, graceful shutdown, parameter optimization, and a cross-platform desktop GUI dashboard.
---

# Trading Bot Development

A complete production-ready trading bot framework with:
- Unified OOP design (`TradingBot` class)
- 3 strategies: Mean Reversion, Trend Following, Swing
- Position persistence and crash recovery
- Graceful shutdown with signal handlers (see `references/safety-features.md`)
- Automated parameter optimization
- Live TUI dashboard for monitoring (see `references/live-dashboard.md`)

## Schwab API Gotchas

| Gotcha | Fix |
|--------|-----|
| `fields=portfolio` / `fields=positions` / `fields=<key>` → 400 | Remove `fields` param entirely, parse full response |
| Account values all `$0.00` | Parse `securitiesAccount` → `currentBalances`/`initialBalances` |
| Futures quotes → 404 | Use `pricehistory` endpoint for all futures data |
| Wrong base URL → silent 404 | Three URLs: `/v1/oauth/`, `/trader/v1/`, `/marketdata/v1/` |
| `hashValue` vs account number | Use hash from `/accounts/accountNumbers`, not plain number |
| Auth code has session param | Parse `code=`, strip `&session=...` |

| Service | Base URL |
|---------|----------|
| OAuth | `https://api.schwabapi.com/v1/oauth/authorize` |
| Trader | `https://api.schwabapi.com/trader/v1/` |
| Market Data | `https://api.schwabapi.com/marketdata/v1/` |

**Pitfall:** Everything does NOT live under `/v1`. Price history is at `/marketdata/v1/pricehistory`, not `/v1/marketdata/pricehistory`.

**Pitfall:** Futures do NOT have a working `/quotes` endpoint. Always use `pricehistory` for all price data, even for latest price.

## Futures Symbol Formats

| Platform | Format |
|----------|--------|
| Schwab API | `/YM`, `/GC`, `/ES`, `/NQ`, `/CL`, `/SI` |
| yfinance | `YM=F`, `GC=F`, `ES=F`, `NQ=F`, `CL=F`, `SI=F` |

## Position Persistence & Graceful Shutdown

See `references/safety-features.md` for:
- JSON position file format
- Signal handler pattern (SIGINT, SIGTERM, SIGHUP)
- Crash recovery on restart
- Position closing on shutdown

## When to Use

- User wants to build a trading bot or automated strategy
- Backtesting trading strategies
- Integrating with broker APIs (Schwab, Alpaca, Interactive Brokers, etc.)
- Optimizing strategy parameters
- Setting up paper trading or live trading workflows

## Core Workflow

### 1. Strategy Definition
Define exact, computer-executable rules:
- Entry criteria (indicators, thresholds, conditions)
- Exit criteria (stop loss, take profit, time-based)
- Position sizing (risk % per trade, max positions)
- Risk management (daily loss limits, kill switches)

**Pitfall:** Vague rules like "I'll know it when I see it" cannot be backtested or automated. Demand specific indicator values.

### 2. Backtesting
Test strategy on historical data before risking capital:
- Use `yfinance` for data (see `references/yfinance-data.md` for 1m chunking workaround)
- Compute indicators (VWAP, Bollinger Bands, RSI, ATR)
- Simulate trades with realistic position sizing
- Track: win rate, profit factor, max drawdown, daily P&L distribution

**Pitfall:** Short backtest periods (7 days) produce unreliable results. Aim for 30+ days minimum. Parameter optimization on small samples overfits.

### 3. Parameter Optimization
Grid search over parameter combinations:
- Test multiple stop loss / profit target multipliers
- Vary indicator thresholds (RSI periods, BB std devs)
- Rank by profit factor and max drawdown, not just total P&L
- Validate on out-of-sample data if possible

### 4. Broker API Integration
Connect to broker for live/paper trading:
- Schwab: OAuth2 flow (see `references/schwab-api.md`)
- Handle token refresh, rate limits, market hours
- Implement paper trading mode first

### 5. Verification
Always verify before running:
- Test indicator calculations with synthetic data
- Test signal generation with known inputs
- Test position sizing math
- Test daily loss limit logic
- Test SL/TP price calculations

Use `scripts/verify_bot.py` as a template.

## Risk Management Rules

| Rule | Typical Value |
|------|---------------|
| Risk per trade | 1-2% of account |
| Max daily loss | 3-5% of account (kill switch) |
| Max positions | 1-3 concurrent |
| Paper trading period | 2-4 weeks minimum |

**Pitfall:** With small accounts (<$1,000), position sizing in shares can make risk management approximate. Accept that 1-share minimums may exceed 2% risk.

## Regulatory Notes

- **Pattern Day Trader (PDT) rule:** Repealed June 4, 2026. FINRA replaced with intraday margin standards. Phase-in period until October 20, 2027. Brokers may still have restrictions.
- Always verify current rules with official sources.

## Common Pitfalls

1. **Wrong base URLs** — OAuth is at `/v1/oauth/`, Trader at `/trader/v1/`, Market Data at `/marketdata/v1`. Mixing these causes 404s.
2. **Invalid account number** — Account info requires `hashValue`, not plain account number. Returns 400 error.
3. **`fields` parameter causes 400 errors** — Schwab returns `{"message":"'portfolio...ields\""}` when `fields=portfolio`, `fields=positions`, or `fields=<any_key>` is passed. Do NOT pass `fields` params to the account endpoint. Fetch full response and parse directly.
4. **Stale prices** — Quote responses have `quote.lastPrice` (live), `extended.lastPrice` (stale), `regular.regularMarketLastPrice`. Always use `quote.lastPrice`.
5. **Price history symbol** — Symbol is a query parameter (`?symbol=AAPL`), not a path parameter.
6. **Overfitting parameters** — optimized backtest results often fail in live trading. Prefer robust parameters over maximum profit.
7. **Ignoring correlation** — trading 2 positions in highly correlated stocks (e.g., FAANG) is effectively one bet.
8. **Binary trade distribution** — if all trades hit either SL or TP with no middle ground, the strategy is working as designed but has no room for partial profits.
9. **Auth code parsing** — OAuth codes may arrive as full URLs with session parameters. Parse `code=` parameter, strip trailing `&session=...`.
10. **yfinance 1m limits** — only ~8 days of 1-minute data per request. Use chunked fetching for longer periods.
11. **Bot appears frozen** — Long-running loops with no output look frozen. Add a status line every iteration showing prices/positions.
12. **404 with empty body** — Usually means token lacks scopes or account not provisioned. Re-authenticate with correct scopes.
13. **PDT rule repealed** — Pattern Day Trader rule was repealed June 4, 2026. Replaced with intraday margin standards.
14. **`tick()` must always reschedule** — If data refresh throws an error and `tick()` doesn't schedule the next call, prices go stale silently. Always wrap in try/except and schedule next tick regardless.
15. **Account values all $0.00** — Caused by passing `fields=portfolio` or `fields=<key>` to Schwab account endpoint. Remove `fields` param, parse full `securitiesAccount` response, check `currentBalances`/`initialBalances` for cash/BP/value.

## CRITICAL Trading Loop Pitfalls (class-level errors that bite implementations)

These bugs are silent and costly — review before every bot launch:

1. **Max positions inside loop** — checking `if len(positions) >= MAX` inside the for-tickers loop allows N entries in one iteration. Fix: check BEFORE the loop. See `references/loop-architecture.md`.
2. **First-loop instant entries** — indicators fire on startup due to no warmup. Fix: skip signal processing on the first loop pass (set `self._first_loop = True`, skip on first iteration).
3. **Silent bot / frozen appearance** — when max positions is reached or market closed, bot sleeps silently for 30+ seconds. Fix: ALWAYS print a status line with prices/positions, even when idle.
4. **Datetime JSON serialization** — `datetime.now()` is not JSON-serializable. Fix: convert to isoformat() before saving, restore with `datetime.fromisoformat()` on load.
5. **Futures quotes don't work** — Schwab has NO working `/quotes` endpoint for futures. Use `pricehistory` for ALL price data including latest price.
6. **Multiple base URLs** — `/v1/oauth`, `/trader/v1`, `/marketdata/v1`. Mixing them causes silent 404s with empty response bodies.
7. **Account hash, not number** — `/accounts/{id}` requires `hashValue` from `/accounts/accountNumbers`, not the plain account number. Returns 400 error otherwise.
8. **Futures symbol format** — `/YM` (Schwab) vs `YM=F` (yfinance). These are DIFFERENT symbols for different platforms.
9. **Repo separation** — Trading bot code and agent config/skills must live in SEPARATE repos. Mixing them causes credential leaks and confusion. See `references/repo-organization.md`.
10. **User workflow: monitoring** — Users want to watch positions in real-time. They don't want to stare at a silent terminal. They may not know the difference between "frozen" and "waiting for signals". Consider: a dedicated dashboard, or at minimum a clear "monitoring..." status that updates with price changes every 30s.
11. **User preference: continuous running** — Users want the bot to run indefinitely until they manually kill it. Don't add auto-shutdown features unless asked.
12. **User preference: paper trading first** — Always start in paper trading mode. Only switch to live trading after explicit user confirmation.
13. **Daily loss resume option** — Users may want to continue trading after hitting daily loss limit. Add `RESUME_ON_DAILY_LOSS` config option (default: True).

## TUI Dashboard Pitfalls (legacy — GUI is now primary)

The TUI was the original dashboard but has been superseded by the native GUI (Flask + pywebview). These pitfalls remain relevant if maintaining `tui.py`:

1. **Stutter / flicker** — Reprinting panels one at a time (multiple `console.print()` calls) combined with `console.clear()` produces visible flicker each interval. Fix: build ONE `Group` from all panels, call `console.clear()` once, then `console.print(scene)` once, then sleep for the remainder of the interval (`max(0.1, REFRESH_INTERVAL - spent)`). Single clear + single print + sleeping remainder. Not avoiding clear() entirely.
2. **Duplication (appearing to stack)** — Rich `Live` does NOT update in non-TTY contexts (pipe, `script -q -c`, `subprocess.Popen(stdout=PIPE)`); in those contexts `Live.update()` emits a full copy each refresh and the output accumulates. Fix: prefer unconditional `clear()`+single-`print(scene)` pattern over `Live`. If you must use `Live`, branch on `console.is_terminal` and fall back to clear+reprint when not a TTY.
3. **Duplication diagnostic** — When the TUI appears to stack copies, run it headless for N seconds, kill it, count occurrences of a unique scene marker (e.g. `'SCALPING BOT'`, `'BID/ASK'`). With a working clear-based refresh the count equals the number of cycles (≈ N / REFRESH_INTERVAL) and stays bounded; with stacking it grows without bound. Status bars appear twice per scene (top + bottom), so `status_bar_count ≈ 2 × scene_count` — that is NOT duplication.
4. **Mockup-driven layout** — When the user shares a visual mockup, match it exactly: panel order, which panels repeat (top + bottom status bar), title alignment (left vs right), border color, text color (light gray vs bright), column structure (e.g. Symbol | Price | Chart | 7c), chart style (classic sparkline chars vs horizontal candle bars vs mini candle bars), placeholder text and style ('N/A', '—', '-'), and spacing. Build what the mockup shows, not what you would have chosen. The mockup in this project had: top "No open positions" box, status bar, SCALPING BOT panel with 2-line body (Cash/BP/Value/Day PnL on line 1, Total PnL + timestamp on line 2), BID/ASK table with green horizontal candle bars in Chart column and '-' in 7c column, POSITIONS panel, bottom status bar.

## Cross-Platform GUI Dashboard (Flask + pywebview)

See `references/gui-dashboard.md` for full architecture, code patterns, and pitfalls.

## Integrated Bot + GUI (GlassTB)

See `references/integrated-gui-bot.md` for the unified app: TradingBot runs as a daemon thread inside the Flask/pywebview app, bot control API routes (`/api/bot/start|stop|status`), trade log persistence, `launch.sh` pattern, and `GUI_MODE` configuration.

### Stack
- **Flask** serves two routes: `/` (JS shell) and `/api/scene` (live HTML fragment)
- **pywebview** opens a native OS window (WebKitGTK on Linux, WebKit on macOS, Edge on Windows)
- **Vanilla JS** in `dashboard.html` polls `/api/scene` every 3s and injects into `#root` via `innerHTML`

### Import Fix (CRITICAL)
`app.py` MUST inject the venv site-packages path at the VERY TOP of the file, BEFORE any other imports:
```python
VENV_SITE_PACKAGES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'venv', 'lib', 'python3.14', 'site-packages'
)
if os.path.isdir(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)
```
Without this, `/usr/bin/python3` cannot find `flask` or `webview`.

### File Paths (CWD-Independent)
All paths (TOKENS_FILE, POSITIONS_FILE, DASHBOARD_FILE, STYLES_FILE) must be relative to `app.py` via `os.path.dirname(os.path.abspath(__file__))`, not CWD.

### Architecture
```
app.py (Flask server + pywebview launcher)
  ├── /           → serves dashboard.html (JS shell with #root + fetch loop)
  └── /api/scene  → returns scene_html() fragment (panels only)
dashboard.html    → standalone JS app: inline <style>, #root div, fetch('/api/scene') loop
styles.css        → dark btop-inspired CSS (may be unused if dashboard.html has inline styles)
```

### Fragment Template (`scene_html()`)
The fragment is pure Python string concatenation — NO Jinja `{{}}` placeholders. Dashboard.html is NOT a template; it's a standalone JS app.

Layout (mockup-matched):
- Top: "No open positions" box (`.top-box`)
- Status bar: `.status-bar` with `.cursor` span + "refresh in 3s • uptime Ns • ctrl+c quit"
- SCALPING BOT panel: title on SAME LINE as Cash/BP/Value/Day PnL metrics
  - Line 2: Total PnL + timestamp (`.ts` right-aligned)
- BID/ASK section: centered header, `.price-table` with columns Symbol | Price | Chart | 7c
  - Chart column: `.bar-fill` (horizontal bar) for /YM, /NQ, /CL, /SI
  - Chart column: `.candle` (OHLC with `.wick` + `.cbody`) for /GC, /ES
  - 7c column: `-` (dash)
- POSITIONS section: centered header with `.pos-header::after` underline divider
  - Box with `.pos-dot` + "No open positions" centered
- Bottom: identical status bar with cursor

### Color Palette
| Element | Color |
|---------|-------|
| Background | `#0a0a12` |
| Panel bg | `#0c0c16` |
| Borders | `#5a7a9a` (light blue) |
| Header/text | `#7ec8e3` (light cyan) |
| Secondary text | `#8aa0b8` |
| Negative PnL | `#e06c75` (red) |
| White cursor | `#ffffff` |

### Common GUI Pitfalls
1. **Import order bug** — `import flask` at top of `app.py` happens before `sys.path` is patched → `/usr/bin/python3` can't find flask/pywebview. Fix: move `sys.path.insert(0, venv_site_packages)` to the VERY TOP of the file.
2. **Jinja confusion** — `dashboard.html` is NOT a Jinja template. It's a standalone JS app with inline `<style>` and a `fetch('/api/scene')` loop. The fragment from `/api/scene` is pure Python string concatenation. Don't mix these two paradigms.
3. **price_html(ticker, ...)` signature** — The function MUST take `ticker` as its first argument. Without it, the candle/bar assignment fails (can't determine if ticker is /GC or /ES for candlestick vs bar).
4. **CWD-dependent paths** — If paths are relative to CWD, the GUI breaks when launched from any directory other than the project root. Fix: use `os.path.dirname(os.path.abspath(__file__))` for all file paths.
5. **`webview.start()` blocks** — The GUI's main thread blocks on `webview.start()`. This means subprocess-based test harnesses will hang. For testing, use Flask's test client (`APP.test_client()`) to verify routes and `scene_html()` output directly, without launching the window.
6. **`gui/__init__.py` required** — For `import gui.app` to work as a package import, the `gui/` directory must contain an `__init__.py` file (can be empty).
7. **Duplicate bot instances** — Before launching the GUI, kill any existing `tui.py` or `gui/app.py` processes to avoid port conflicts.
8. **String concatenation in return tuples** — `return ('<div>' '<span>' '</div>')` looks like string concatenation but creates a tuple of strings — invalid HTML output and causes SyntaxError on closing paren. Use `'<div>' + '<span>' + '</div>'` or `''.join([...])` patterns.
9. **Stop button must flip immediately** — `stop_bot()` must set `state['bot_running']=False` and `status='idle'` immediately. Use `_bot_run_wrapper()` for daemon thread, don't wait for thread exit.
10. **Chart rendering matters** — Candles must be 16px wide with absolute-positioned wick+body (`top:Npx;height:Mpx`). Bars must use `log10` scale so small-priced assets are visible alongside large ones.
11. **Schwab API rejects `fields` param** — Returns 400 `{"message":"'portfolio...ields\""}`. Fetch full response and parse manually.
12. **Tick resilience** — `tick()` must always reschedule the next call in a `try/except`, even when `fetch_data_sync()` throws.
13. **Duplicate UI sections** — Remove redundant top "No open positions" box and bottom status bar (mockup had them, user later removed them).
14. **No 7c column** — User explicitly removed the 7c column. BID/ASK table has only: Symbol, Price, Chart.
15. **Schwab account structure** — Full response structure: `securitiesAccount.positions[].{longQuantity, shortQuantity, marketValue, averagePrice}`, `securitiesAccount.currentBalances.{cashAvailableForTrading, availableFunds, buyingPower}`, `securitiesAccount.initialBalances.{liquidationValue}`.
16. **Value fallback** — When account has no positions, `value` should equal `cash` (not 0), otherwise the user sees all zeros and thinks data isn't loading.

## Support Files

- `references/schwab-api.md` — Schwab API OAuth2 flow, endpoints, quirks
- `references/yfinance-data.md` — Data fetching workarounds and limitations
- `references/quote-data-structure.md` — Quote response field breakdown (lastPrice vs extended.lastPrice)
- `references/safety-features.md` — Position persistence, graceful shutdown, signal handlers
- `references/loop-architecture.md` — Trading loop patterns: max positions, first loop, silent bot, datetime serialization
- `references/repo-organization.md` — Two-repo structure, cross-repo .gitignore patterns
- `references/live-dashboard.md` — Real-time TUI dashboard with prices, sparklines, positions (Rich or Textual); includes stutter/flicker pitfall and mockup-driven layout guidance
- `references/new-live-dashboard.md` — Updated live-dashboard reference with single-pass clear+print pattern, TTY/pipe duplication diagnostic, Live-does-not-update-in-pipes note, mockup-driven layout checklist
- `references/live-dashboard-v2.md` — Same updated live-dashboard content under an alternate filename (kept for reference)
- `references/tui-token-refresh.md` — TUI token refresh handling