---
name: trading-bot-development
description: End-to-end development of automated trading bots — strategy design, backtesting, parameter optimization, risk management, and live execution via broker APIs (Schwab, Alpaca, etc.)
triggers:
  - trading bot
  - automated trading
  - mean reversion
  - scalping strategy
  - backtesting
  - schwab api
  - alpaca api
  - algorithmic trading
  - quantitative trading
  - trading strategy
  - live trading
---

# Trading Bot Development

Build automated trading systems from strategy design through live execution.

## Strategy Design

### Mean Reversion
- Entry when price extends beyond VWAP + RSI extreme + Bollinger Band touch
- Short timeframes (1-5 min bars) for scalping
- Common indicators: VWAP, Bollinger Bands, RSI, ATR

### Trend Following
- EMA crossovers, pullback entries in direction of trend
- Often underperforms mean reversion in backtests — verify with data
- Can be removed if backtest shows consistent losses

### Key Principle
- Let backtest results drive strategy composition
- Kill components that lose money regardless of theoretical appeal
- Mean reversion + trend following often conflicts; test both separately first

## Backtesting Framework

### Data Sources
- **yfinance**: Free but limited (1m data ~8 days per request, 30 days max)
  - Use `Ticker.history(period='7d', interval='1m')` — works better than `yfinance.download()`
  - Fetch multiple chunks and combine for longer backtests
- **Polygon.io**, **Alpaca**, **Schwab**: Better historical data, API keys required

### Parameter Optimization
- Grid search over parameter combinations (SL multiplier, TP multiplier, RSI thresholds)
- Test 50-100+ combinations for robustness
- Use walk-forward optimization: optimize on in-sample, validate on out-of-sample
- Look for parameter stability — if only one combo works, it's likely overfit

### Key Metrics
- **Profit Factor**: Gross profits / gross losses (want > 1.1)
- **Win Rate**: Not as important as reward-to-risk ratio
- **Max Drawdown**: Should be < 30% of account for survivability
- **Trade Distribution**: Binary outcomes (hit SL or TP) indicate systematic execution

## Risk Management

### Position Sizing
```
risk_amount = account_value * risk_pct  # typically 1-2%
stop_distance = ATR * stop_multiplier
qty = max(1, int(risk_amount / stop_distance))
```

### Daily Loss Limits
- Hard kill switch at 3-5% daily drawdown
- Stop trading for the day when hit
- Prevents emotional/revenge trading

### Position Limits
- Max concurrent positions (1-2 for small accounts)
- Correlated tickers (e.g., FAANG stocks) count as partial same bet
- With <$1,000: 1 position max is safer

## Schwab API Integration

### Setup
1. Register at https://developer.schwab.com/
2. Create app with redirect URI `https://127.0.0.1:8080`
3. Select scopes: MarketData, AccountAccess, Trade, Orders
4. Get App Key and App Secret
5. Order limit: set to 50-100/day for small accounts

### Critical: API URL Structure
Schwab uses **different base URLs** for different endpoints. Using the wrong base URL causes 404 errors:

| Category | Base URL |
|----------|----------|
| OAuth (authorize, token) | `https://api.schwabapi.com/v1/oauth/...` |
| Trader (accounts, orders) | `https://api.schwabapi.com/trader/v1/...` |
| Market Data (quotes, history) | `https://api.schwabapi.com/marketdata/v1/...` |

**Wrong** (common mistake):
```python
self.base_url = 'https://api.schwabapi.com/v1'
self.market_data_url = f'{self.base_url}/marketdata/{symbol}/quotes'  # 404!
```

**Correct**:
```python
self.base_url = 'https://api.schwabapi.com/v1'
self.market_data_url = 'https://api.schwabapi.com/marketdata/v1'
self.trader_url = 'https://api.schwabapi.com/trader/v1'
```

### Stocks vs Futures Symbol Format

| Platform | Stocks | Futures |
|----------|--------|---------|
| Schwab API | `AAPL`, `GOOGL` | `/YM`, `/GC`, `/ES`, `/NQ`, `/CL`, `/SI` |
| yfinance | `AAPL`, `GOOGL` | `ES=F`, `NQ=F`, `YM=F`, `CL=F`, `GC=F`, `SI=F` |

**Important**: Futures quotes via `/marketdata/v1//YM/quotes` do NOT work on Schwab. Use price history endpoint to get latest prices for futures.

### Account Info: Use hashValue, NOT accountNumber

The `/accounts/accountNumbers` endpoint returns:
```json
[{"accountNumber": "56781519", "hashValue": "968DE78C99FF469850398683B7A40052F210137C15E21EC87668DAD3FEB1C898"}]
```

**Wrong** (causes 400 "Invalid account number"):
```python
self.account_id = accounts[0].get('accountNumber')
```

**Correct**:
```python
self.account_id = accounts[0].get('hashValue')
```

### Quote Data Structure

Live quote data is nested. Always check `quote` first (live data), then fallback to `extended` (stale/closing data):

```python
# Correct order for live prices
last_price = ticker_data.get('quote', {}).get('lastPrice', 0)
if last_price == 0:
    last_price = ticker_data.get('extended', {}).get('lastPrice', 0)
```

### Authentication (OAuth2)
- Authorization code flow with local server callback
- **Critical**: Local HTTP server CANNOT capture HTTPS redirects — user must manually copy code from browser URL
- Fallback: manual code entry from browser URL if localhost redirect fails
- Authorization codes are single-use and expire quickly
- **Parse carefully**: Code may arrive as `CODE&session=SESSION` — split on `&` and use only the code portion
- Tokens saved to file; refresh automatically before expiry
- Market data access may take hours/days to activate after app approval

### Paper Trading Gate
- Always implement a `paper_trading` config flag
- When True: NO orders are placed, signals print `[PAPER TRADE]` only
- When False: orders are placed via API
- Start with `paper_trading: True` and only flip after weeks of successful paper trading

### Key Endpoints
- `/v1/accounts/accountNumbers` — get account ID
- `/v1/marketdata/{symbol}/pricehistory` — historical bars
- `/v1/marketdata/{symbol}/quotes` — current quote (bid, ask, last)
- `/v1/accounts/{id}/orders` — place/check orders

### Order Types
- MARKET: Immediate execution
- LIMIT: Price-controlled entry
- Always use DAY duration for intraday strategies
- **Always attach SL/TP** — bracket orders or separate exit orders

## Main Loop Safety Requirements

The main loop MUST implement these safety features. Without them, the bot WILL lose money.

### Position Tracking
- Maintain a dict: `open_positions[ticker] = {'side', 'qty', 'entry', 'sl', 'tp', 'entry_time'}`
- Check this dict before entering — block duplicate entries for same ticker
- Clear all positions at market open each day

### Exit Monitoring
- Poll positions every 30 seconds for SL/TP hits
- For longs: close if price <= SL or price >= TP
- For shorts: close if price >= SL or price <= TP
- Close all remaining positions at 4:00 PM (market close)

### Daily Loss Limit
- Calculate dynamically: `daily_loss_limit = -(account_value * max_daily_loss_pct)`
- Never hardcode a dollar amount
- Stop trading for the day when `daily_pnl < daily_loss_limit`

### Max Positions
- Check `len(open_positions) < max_positions` before new entries
- With correlated tickers (FAANG), consider 1 position max

### Account Info Caching
- Do NOT call `get_account_info()` every tick — rate limit risk
- Cache and update only on signal or every N iterations

## Verification Pattern

After ANY code change, write a small **ad-hoc verification script** that imports the actual functions and tests behavior. Delete it after passing.

### Test Categories
1. Indicator calculations (VWAP, BB, RSI, ATR)
2. Signal generation (long/short/none, boundary conditions)
3. Position sizing (2% risk, min 1 share)
4. Exit conditions (SL/TP for long/short)
5. Daily loss limit (dynamic calculation, not hardcoded)
6. Position tracking (add/remove/duplicate blocking)
7. Market close handling (close all, calculate P&L)

### Why Ad-Hoc?
Static scripts (like `scripts/verify_bot.py`) go stale. Writing fresh tests for each change ensures the tests match the current code. Think of it as "trust but verify" — the existing script is a reference template, not a substitute for fresh verification.

## Common Pitfalls

### PDT Rule (Pattern Day Trader)
- **Repealed June 4, 2026** — FINRA replaced with intraday margin standards
- Old rule: 3 day trades per 5 days for margin accounts <$25k
- Phase-in period until October 2027 — check broker-specific implementation

### yfinance Data Limits
- 1m data: max ~8 days per request, 30 days total lookback
- Workaround: fetch multiple chunks with `Ticker.history()` and combine
- Multi-level columns may need flattening: `df.columns = df.columns.get_level_values(0)`

### Bollinger Bands %B
- Can go below 0 (below lower band) or above 1 (above upper band)
- This is normal and expected — don't assert it's within [0,1] in tests
- The strategy uses < 0.1 (oversold) and > 0.9 (overbought) thresholds

### VWAP Calculation
- Must reset daily for intraday strategies
- Use typical price: `(High + Low + Close) / 3`
- Cumulative volume * typical price / cumulative volume
## File Structure

```
trading-bot/
├── live_bot.py              # Main bot with strategy + API client
├── backtest.py              # Backtesting and optimization
├── requirements.txt         # Dependencies
├── tokens.json              # OAuth tokens (gitignored)
├── .gitignore               # Exclude tokens, venv, data files
└── README.md                # Strategy overview
```

## GUI Integration (Optional)

For a single cohesive app combining bot + dashboard:

- Use Flask + pywebview (cross-platform native window)
- Run `TradingBot.run()` in a background daemon thread
- Expose `/api/bot/start`, `/api/bot/stop`, `/api/bot/status` API routes
- Add `Config.GUI_MODE = True` to disable blocking `input()` prompts

See `schwab-trader-api/references/gui-bot-integration.md` for the complete pattern.

## Dependencies
```
requests>=2.28.0
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.0  # for backtesting only
```

## Verification Checklist
- [ ] All indicator calculations return valid values
- [ ] Signal generation produces expected LONG/SHORT/NONE
- [ ] Position sizing never risks more than 2% per trade
- [ ] Daily loss limit triggers correctly
- [ ] SL/TP prices calculate correctly for both long and short
- [ ] Market hours check prevents trading outside 9:30-16:00 ET
- [ ] Authentication flow works (OAuth2 or PAT)

## References

- `references/schwab-api.md` — Schwab API endpoints, auth flow, rate limits
- `references/strategy-patterns.md` — Mean reversion, trend following implementations
- `references/backtesting-methods.md` — Walk-forward optimization, parameter stability
- `templates/live_bot.py` — Starter bot template with Schwab API client
- `scripts/verify_bot.py` — Verification script for bot logic
