---
name: trading-bot
description: Production-ready automated trading bot framework for stocks and futures via Schwab API. Includes mean reversion, trend following, and swing strategies with safety features.
tags: [trading, backtesting, schwab, api, automation, finance, futures, bot]
---

# Trading Bot Development

A complete production-ready trading bot framework with:
- Unified OOP design (`TradingBot` class)
- 3 strategies: Mean Reversion, Trend Following, Swing
- Position persistence and crash recovery
- Graceful shutdown with signal handlers (see `references/safety-features.md`)
- Automated parameter optimization

## Critical API Architecture

Schwab uses **THREE distinct base URLs** — using the wrong one causes silent 404s:

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

1. **Wrong base URLs** — OAuth is at `/v1/oauth/`, Trader at `/trader/v1/`, Market Data at `/marketdata/v1/`. Mixing these causes 404s.
2. **Invalid account number** — Account info requires `hashValue`, not plain account number. Returns 400 error.
3. **Stale prices** — Quote responses have `quote.lastPrice` (live), `extended.lastPrice` (stale), `regular.regularMarketLastPrice`. Always use `quote.lastPrice`.
4. **Price history symbol** — Symbol is a query parameter (`?symbol=AAPL`), not a path parameter.
5. **Overfitting parameters** — optimized backtest results often fail in live trading. Prefer robust parameters over maximum profit.
6. **Ignoring correlation** — trading 2 positions in highly correlated stocks (e.g., FAANG) is effectively one bet.
7. **Binary trade distribution** — if all trades hit either SL or TP with no middle ground, the strategy is working as designed but has no room for partial profits.
8. **Auth code parsing** — OAuth codes may arrive as full URLs with session parameters. Parse `code=` parameter, strip trailing `&session=...`.
9. **yfinance 1m limits** — only ~8 days of 1-minute data per request. Use chunked fetching for longer periods.
10. **Bot appears frozen** — Long-running loops with no output look frozen. Add a status line every iteration showing prices/positions.
11. **404 with empty body** — Usually means token lacks scopes or account not provisioned. Re-authenticate with correct scopes.
12. **PDT rule repealed** — Pattern Day Trader rule was repealed June 4, 2026. Replaced with intraday margin standards.

## Common Pitfalls (Trading Loop Specific)

These are class-level errors that bite trading bot implementations:

1. **Max positions inside loop** — checking `if len(positions) >= MAX` inside the for-tickers loop allows N entries per iteration. See `references/loop-architecture.md`.
2. **First-loop instant entries** — indicators produce signals on startup due to warmup. Skip signal processing on the first loop pass.
3. **Silent bot / frozen appearance** — when max positions is reached or outside market hours, the bot sleeps silently. Always print status.
4. **Datetime JSON serialization** — `datetime.now()` is not JSON serializable. Convert to isoformat() before saving, restore after loading.
5. **Futures quotes don't work** — Schwab has no working `/quotes` endpoint for futures. Use `pricehistory` for everything.
6. **Multiple base URLs** — `/v1/oauth`, `/trader/v1`, `/marketdata/v1`. Mixing them causes silent 404s.
7. **Account hash, not number** — use `hashValue` from `/accounts/accountNumbers`, not plain account number.

## Support Files

- `references/schwab-api.md` — Schwab API OAuth2 flow, endpoints, quirks
- `references/yfinance-data.md` — Data fetching workarounds and limitations
- `references/safety-features.md` — Position persistence, graceful shutdown, signal handlers
- `references/loop-architecture.md` — Trading loop patterns: max positions, first loop, silent bot, datetime serialization
- `scripts/verify_bot.py` — Verification script template

## API URL Architecture

Schwab uses THREE distinct base URLs:
- OAuth: `https://api.schwabapi.com/v1/oauth/authorize`
- Trader: `https://api.schwabapi.com/trader/v1/...`
- Market Data: `https://api.schwabapi.com/marketdata/v1/...`

**Pitfall:** Futures do NOT have a working `/quotes` endpoint. Use `pricehistory` for all price data.

**Pitfall:** Symbol is a query parameter (`?symbol=AAPL`), not a path parameter.
