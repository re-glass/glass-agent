---
name: schwab-trader-api
description: Build trading bots and automated strategies using the Charles Schwab Trader API. Covers OAuth2 auth, market data endpoints, order placement, token management, and the progression from backtesting to live trading.
triggers:
  - schwab api
  - trading bot
  - automated trading
  - broker api
  - mean reversion bot
  - day trading bot
  - stock scalping
  - market data integration
---

# Schwab Trader API Integration

Build trading bots that connect to Charles Schwab's official API for market data, account management, and order execution.

## Architecture Overview

The Schwab API has **three separate base URL spaces** that must not be confused:

| Purpose | Base URL |
|---------|----------|
| OAuth (authorize, token) | `https://api.schwabapi.com/v1/oauth/...` |
| Trader (accounts, orders) | `https://api.schwabapi.com/trader/v1/...` |
| Market Data (quotes, price history) | `https://api.schwabapi.com/marketdata/v1/...` |

**Critical:**
- OAuth is at `/v1/oauth/...` — NOT `/trader/v1/oauth/...`
- Account endpoints are under `/trader/v1/...`, NOT `/v1/...`
- Market data endpoints are under `/marketdata/v1/...`
- These are the #1, #2, and #3 integration pitfalls.

## Authentication Flow

### OAuth2 Setup
1. Create app at https://developer.schwab.com/
2. Redirect URI: `http://localhost:8080` or `https://127.0.0.1:8080`
3. Request scopes: `MarketData`, `AccountsAndTrading`
4. App status must show "Ready for Use" (not just "Pending")

### Token Exchange
Authorization codes from Schwab may include a trailing `&session=...` parameter. Strip it before exchanging for tokens. The bot should handle both raw codes and full redirect URLs.

Tokens are saved to a local file (`tokens.json`) and auto-refreshed when expired. The refresh token typically lasts 7 days.

### Manual Fallback
The local HTTP server at `localhost:8080` often fails because Schwab's portal uses HTTPS redirect URIs. Always implement a manual fallback: user copies the `code=` parameter from the browser's address bar and pastes it into the terminal.

## Market Data Endpoints
### Price History
```
GET /marketdata/v1/pricehistory?symbol=AAPL&periodType=day&period=1&frequencyType=minute&frequency=1
```

**Note:** `symbol` is a query parameter, NOT a path parameter. This differs from quotes.
GET /marketdata/v1/chains (options)
GET /marketdata/v1/expirationchain (options)
GET /marketdata/v1/quotes (batch)
```

Price history parameters:
- `periodType`: `day`, `month`, `year`, `ytd`
- `period`: number of periods (e.g., `5` for 5 days)
- `frequencyType`: `minute`, `daily`, `weekly`, `monthly`
- `frequency`: `1`, `5`, `10`, `15`, `30` (minutes) or `1` (daily/weekly/monthly)

**Rate Limits:** ~120 requests/minute for standard accounts.

## Account & Trading Endpoints (under /trader/v1)

```
GET /trader/v1/accounts/accountNumbers
GET /trader/v1/accounts/{accountHash}?fields=positions
POST /trader/v1/accounts/{accountHash}/orders
GET /trader/v1/accounts/{accountHash}/orders
```

**Critical:** Use the `hashValue` from `accountNumbers` response, NOT the plain `accountNumber`. Using the plain number returns `400 Invalid account number`.

Order structure:
```python
{
    'session': 'NORMAL',
    'duration': 'DAY',
    'orderType': 'MARKET',  # or 'LIMIT'
    'quantity': 10,
    'symbol': 'AAPL',
    'instruction': 'BUY',  # or 'SELL'
}
```

Add `'price': limit_price` for LIMIT orders.

## Backtest-to-Live Workflow

Always progress through these stages in order:

1. **Strategy Design** — Define exact entry/exit rules, indicators, thresholds
2. **Backtesting** — Test against historical data (yfinance for prototyping)
3. **Parameter Optimization** — Grid search over indicator thresholds, stop/target multipliers
4. **Paper Trading** — Run bot with `paper_trading: True` for 2-4 weeks minimum
5. **Live Trading** — Only after consistent paper performance

### Backtest Requirements
- Minimum 30 days of data for scalping strategies
- Include realistic slippage estimates
- Track max drawdown, profit factor, win rate, trade distribution
- Walk-forward optimization (test on out-of-sample periods)
## Live Trading Safety

- Start with `paper_trading: True` gate that prevents all real orders
- Implement daily loss limit (e.g., 5% of account) as a hard kill switch
- Track open positions in-memory; never place duplicate entries
- Monitor positions for SL/TP exits every tick
- Close all positions at market end-of-day
- **Graceful shutdown**: Signal handlers close all positions on Ctrl+C/kill
- **Position persistence**: Save positions to file for crash recovery

### Graceful Shutdown Pattern
```python
import signal

def _setup_signal_handlers(self):
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)

def _signal_handler(self, signum, frame):
    self._close_all_positions()  # Closes all positions at market
    sys.exit(0)
```

### Position Persistence Pattern
Save to `positions.json` on every change. On restart, load positions from same day to recover from crashes. Convert datetime objects to strings for JSON serialization.

## Common Pitfalls

### Wrong Base URL (Critical)
Schwab has THREE separate base URL spaces:
- OAuth: `https://api.schwabapi.com/v1/oauth/...`
- Trader: `https://api.schwabapi.com/trader/v1/...`
- Market Data: `https://api.schwabapi.com/marketdata/v1/...`

Using `/v1/` for everything causes 404s on all market data endpoints.

### Account Hash vs Plain Number (Critical)
`/accounts/accountNumbers` returns both `accountNumber` and `hashValue`. **Use `hashValue`** for all account-specific endpoints. Plain `accountNumber` returns `400 Invalid account number`.

### Schwab API Rejects `fields` Query Param (Critical)
Schwab returns `400 Bad Request` with a cryptic error when you pass `?fields=portfolio` or `?fields=<key>`. **Do not use the `fields` parameter.** Fetch the full account response and parse it manually:
```python
r = requests.get(f'https://api.schwabapi.com/trader/v1/accounts/{hash}', headers=headers, timeout=10)
body = r.json()
acct = body.get('securitiesAccount') or body
positions = acct.get('positions', [])
balances = acct.get('currentBalances') or acct.get('initialBalances') or {}
cash = balances.get('cashAvailableForTrading') or balances.get('availableFunds') or 0.0
```

### Tick/Data Refresh Resilience
`tick()` must always reschedule the next call even if `fetch_data_sync()` throws. Otherwise the GUI freezes on the first error.

### Stop Bot Button State
`stop_bot()` must set `state['bot_running']=False` and `status='idle'` immediately — users reject delays. Use a `_bot_run_wrapper()` that also resets state on natural exit.

### Price History Symbol Parameter
`pricehistory` takes `symbol` as a **query parameter**, not a path parameter:
```
GET /marketdata/v1/pricehistory?symbol=AAPL&...
```
While quotes use it in the path:
```
GET /marketdata/v1/AAPL/quotes
```

### Futures Implementation Notes
- **Futures quotes via `/marketdata/v1/{symbol}/quotes` return 404** — this endpoint only works for equities
- Use `get_latest_price()` with price history for all futures price data
- **Futures symbol format for Schwab:** Use `/YM`, `/GC`, `/ES` (not `YM=F`) — the `/` prefix denotes futures
- **yfinance format:** Use `ES=F`, `YM=F` for backtesting data
- Same indicator logic (VWAP, BB, RSI, ATR) applies to futures
- Position sizing must account for contract multiplier

### Empty 404 Responses on All Endpoints
If all endpoints return 404 with empty response body:
- Token issued before app fully approved → delete `tokens.json`, re-authenticate
- Market data not provisioned → wait 24-72 hours after approval
- Account restriction → call Schwab: 1-800-435-4000

### Stale vs Live Prices (Critical)
Quote responses contain **two different prices**:
```json
{
  "extended": {"lastPrice": 77.78},    // ← STALE (snapshot/delayed)
  "quote": {"lastPrice": 77.335}       // ← LIVE (use this!)
}
```
Always use `quote.lastPrice` for trading decisions. Using `extended.lastPrice` causes trades based on stale data. Apply this to status displays, entry prices, and SL/TP monitoring.

### Auth Code Parsing
Schwab auth codes are often returned with trailing `&session=...` in the URL. Strip before exchanging:
```python
code = raw.split('&')[0].strip()
```
Also handle users pasting full redirect URLs vs raw codes.

### PDT Rule Status
FINRA's Pattern Day Trader ($25k minimum) rule was **repealed June 4, 2026**, replaced with intraday margin standards. Small accounts are no longer PDT-restricted.

### FAANG Stock Characteristics
- Highly correlated (2 positions = effectively 1 bet)
- AAPL may underperform vs GOOGL/META/NFLX in mean reversion
- Consider limiting universe to top performers

## Futures Markets (Alternative to Stocks)

Futures offer nearly 24-hour trading vs 6.5 hours for stocks. Same mean reversion logic applies.

### Available Futures via yfinance
| Ticker | Market | Hours |
|--------|--------|-------|
| `ES=F` | S&P 500 E-mini | ~23h/day |
| `NQ=F` | Nasdaq 100 E-mini | ~23h/day |
| `YM=F` | Dow Jones E-mini | ~23h/day |
| `CL=F` | Crude Oil | ~23h/day |
| `GC=F` | Gold | ~23h/day |
| `SI=F` | Silver | ~23h/day |

### Backtest Results (Mean Reversion, 7 days, 1m bars)
Top performers from a session backtest:
- **SI=F (Silver)**: 114 trades, 49.1% win rate, +$519.97 P&L, PF=1.45
- **CL=F (Crude Oil)**: 212 trades, 42.0% win rate, +$208.40 P&L, PF=1.08
- **ES=F (S&P 500)**: 33 trades, 45.5% win rate, +$103.43 P&L, PF=1.32

### Key Differences from Stocks
- **More trading hours** = more signal opportunities
- **Higher volatility** = wider stops needed
- **Contract sizes** differ (ES = $50/point, CL = $1000/point)
- **Margin requirements** vary by contract
- **Rollover dates** require attention (contracts expire monthly/quarterly)

### Implementation Notes
- Use `yfinance.download('ES=F', period='7d', interval='1m')` for data
- Same indicator logic (VWAP, BB, RSI, ATR) applies
- Position sizing must account for contract multiplier
- Monitor for contract expiration/rollover
- **Futures quotes return 404** — use `get_latest_price()` with price history for all price data
- **Futures symbol format:** Use `/YM`, `/GC`, `/ES` (not `YM=F`) for Schwab API price history

## Cross-Platform GUI

For building a native-window dashboard that runs on any PC (Windows, macOS, Linux), use **Flask + pywebview** instead of tkinter/PyQt:

- Flask serves a dark dashboard on localhost
- pywebview opens a native window (WebKitGTK on Linux, WebKit on macOS, Edge on Windows)
- JS frontend polls `/api/scene` every 3s and injects HTML into `#root`
- `launch.sh` in project root: `chmod +x launch.sh && ./launch.sh`
- Dashboard title: **GlassTB** (not "Trading Bot")

**Why:** tkinter often broken (missing TK libs), PyQt5/customtkinter not installed, no Rust toolchain for Tauri. pywebview installs cleanly into venv.

**Critical fixes:**
1. `sys.path.insert(0, venv_site_packages)` at VERY TOP of `app.py` (before import flask)
2. `price_html(ticker, price)` takes ticker as first arg — reverse-lookup from price fails when no data
3. CWD independence: `os.path.dirname(os.path.abspath(__file__))` for all file paths
4. Bot runs as daemon thread; GUI_MODE=True skips signal handlers and blocking input()
5. Schwab returns `400` on `?fields=portfolio` or any `?fields=<key>` — fetch full response and parse manually
6. `tick()` must always reschedule (try/except + reschedule in finally) or GUI freezes on error
7. `stop_bot()` must set `state['bot_running']=False` immediately — users reject delayed button flips
8. Account values come from `securitiesAccount.currentBalances` or `initialBalances` (try both); fallback `value=cash` if no positions

**User preferences (2026-09-17):**
- No duplicate UI sections — removed top `No open positions` box and bottom status-bar
- No `7c` column — removed from BID/ASK table
- **No chart column** — user removed both candles and bars; table is Symbol + Price only
- Window/repo name: **GlassTB**
- Repo: https://github.com/re-glass/GlassTB

## Integrating Bot + GUI

For a single app that combines the trading bot and dashboard:

- Run `TradingBot.run()` in a background daemon thread
- Expose `/api/bot/start`, `/api/bot/stop`, `/api/bot/status` Flask routes
- Render bot control panel (Start/Stop buttons, status indicator, strategy/mode) on dashboard
- Render trade log panel (last 50 trades with time, symbol, side, qty, price, P&L, reason)
- Use `Config.GUI_MODE = True` to disable blocking `input()` prompts (auto-continue on daily loss)
- Skip signal handlers in GUI mode (only main thread can set signals)

See `references/gui-bot-integration.md` for the complete integration pattern including thread management, Flask routes, HTML/JS for bot control panel, and state management.

## See Also

- `references/schwab-api-endpoints.md` — Endpoint reference with verified URLs (CRITICAL: `/trader/v1` not `/v1`)
- `references/integration-pitfalls.md` — Session-learned pitfalls (URL structures, redirect issues, 404 causes)
- `references/futures-integration.md` — Futures trading: quotes don't work, use price history for everything
- `references/futures-bot-implementation.md` — Bug fixes, contract sizing, multi-strategy results
- `references/main-loop-structure.md` — Verified main loop with position tracking and SL/TP monitoring
- `references/live-vs-stale-prices.md` — Quote response structure: `quote.lastPrice` (live) vs `extended.lastPrice` (stale)
- `references/auth-code-parsing.md` — How to strip `&session=...` from auth codes
- `references/multi-strategy-testing.md` — Strategy definitions, symbol formats, backtest results
- `references/gui-flask-pywebview.md` — Cross-platform GUI: Flask + pywebview native window, mockup layout
- `templates/live_bot.py` — Working bot template
- `scripts/verify_connection.py` — Diagnostic script to test API connectivity

## File References

- `references/schwab-api-endpoints.md`
- `references/integration-pitfalls.md`
- `references/main-loop-structure.md`
- `references/futures-integration.md`
- `templates/live_bot.py`
- `scripts/verify_connection.py`
