---
name: algorithmic-trading
description: End-to-end workflow for developing, backtesting, optimizing, and deploying algorithmic trading strategies. Covers strategy specification, parameter optimization, trade distribution analysis, broker API integration, and verification.
tags:
  - trading
  - backtesting
  - strategy
  - optimization
  - schwab
  - yfinance
---

# Algorithmic Trading Skill

## Overview

This skill covers the complete workflow for building algorithmic trading strategies — from initial specification through backtesting, optimization, verification, and live deployment.

## Workflow

### 1. Strategy Specification

Before coding, define the strategy in plain language:

1. **Markets & Universe**: Which tickers? (e.g., FAANG, SP500, sector-specific)
2. **Timeframe**: 1-min, 5-min, hourly, daily?
3. **Strategy Type**: Mean reversion, trend following, breakout, hybrid?
4. **Indicators**: VWAP, Bollinger Bands, RSI, EMA, ATR, MACD?
5. **Entry Rules**: Exact conditions (AND vs OR logic)
6. **Exit Rules**: Stop loss, take profit, time-based, indicator-based
7. **Risk Rules**: Max risk per trade, max daily loss, max position count

**Rule of thumb**: If you cannot express the strategy as boolean conditions, it is not ready to code.

### 2. Initial Backtest

- Start with a **standard/default parameter set** before optimizing
- Use recent data (7-30 days for intraday, longer for swing)
- Look at win rate, profit factor, P&L, max drawdown, trade distribution, exit reasons

**Critical**: Always check if a strategy component is losing money. If so, consider removing it rather than tuning it. (Example: trend following was a major drag in a mean reversion system; removing it turned a losing strategy into a profitable one.)

### 3. Parameter Optimization

- Grid search over reasonable parameter ranges
- Key parameters: ATR multipliers, RSI thresholds, BB settings
- Test 50-100+ combinations
- Look for **robust** parameters (profitable across multiple combos), not just the single best

### 4. Trade Distribution Analysis

A clean trade distribution is a sign of a systematic, rule-based strategy:

- **Binary outcomes**: Trades cluster near SL and TP prices (good — systematic)
- **Spread outcomes**: Trades scattered across P&L range (bad — discretionary or noisy)
- **Concentration**: Top 10 trades should not account for >50% of P&L
- **Streaks**: Max win/loss streaks tell you about psychological tolerance

### 5. Verification

Before live deployment, write ad-hoc tests that verify:

1. Indicator calculations produce expected values
2. Signal generation fires correctly (LONG/SHORT/NONE, boundary conditions)
3. Position sizing respects risk limits
4. Daily loss limit triggers correctly
5. Market hours filtering works
6. SL/TP prices are calculated correctly

### 6. Live Deployment

**Always paper trade first.** No exceptions. Run for 2-4 weeks minimum before live capital.

## Broker Selection

| Broker | API | Recommendation |
|--------|-----|----------------|
| **Schwab** | Official, OAuth2 | **Preferred** for live trading |
| Robinhood | None (unofficial, ToS violation) | Avoid |
| Interactive Brokers | Official, complex | Good for advanced use |
| Alpaca | Official, simple | Good for beginners |

**Key insight**: Robinhood does not offer a public API. Using unofficial libraries violates their ToS and risks account termination.

## Schwab App Setup

When creating a Schwab app at https://developer.schwab.com/:

### Required Scopes
- **MarketData Production** — for quotes and price history
- **Accounts and Trading Production** — for placing orders and checking positions

### Redirect URI
- Use `http://localhost:8080` for local development
- Some portals require `https://localhost:8080`
- If neither works, use any valid URL (e.g., `https://example.com/callback`) — the bot has a manual fallback where you paste the authorization code from the browser

### Order Limit
- For small accounts (<$1,000), set to 50-100 orders/day
- This provides safety headroom without being restrictive

### App Name
- Any name works (e.g., "Scalping Bot") — it's just for your reference in the portal

## Data Source: yfinance

### 1-Minute Data Limitation

yfinance limits 1-minute data to approximately **8 days per request**.

### Data Fetching Pattern

```python
import yfinance as yf

# Good — works reliably
t = yf.Ticker('AAPL')
data = t.history(period='7d', interval='1m')

# Bad — often fails with large date ranges
data = yf.download('AAPL', start='2025-01-01', end='2025-09-01', interval='1m')
```

### Fetching Multiple Chunks

To get more than 8 days of 1m data, fetch multiple chunks and combine:

```python
def fetch_extended_1m(ticker, chunks=6, chunk_days=8):
    all_data = []
    end_date = datetime.now()
    for i in range(chunks):
        chunk_start = end_date - timedelta(days=chunk_days * (i + 1))
        chunk_end = end_date - timedelta(days=chunk_days * i)
        t = yf.Ticker(ticker)
        data = t.history(
            start=chunk_start.strftime('%Y-%m-%d'),
            end=chunk_end.strftime('%Y-%m-%d'),
            interval='1m'
        )
        if not data.empty:
            all_data.append(data[['Open', 'High', 'Low', 'Close', 'Volume']])
    return pd.concat(all_data) if all_data else pd.DataFrame()
```

## Regulatory Notes

### Pattern Day Trader (PDT) Rule

**REPEALED as of June 4, 2026.** FINRA replaced the old PDT rule (which required $25k minimum equity and limited traders to 3 day trades per 5 days) with new intraday margin standards. Brokers have until October 20, 2027 to fully implement.

## Risk Management Defaults

| Parameter | Conservative | Standard | Aggressive |
|-----------|-------------|----------|------------|
| Risk per trade | 1% | 2% | 5% |
| Max daily loss | 3% | 5% | 10% |
| Max positions | 1 | 2 | 5 |

**Never exceed 5% risk per trade. Never.**

## Pitfalls

1. **Overfitting**: The best backtest parameters often fail in live trading. Prefer robust parameters.
2. **Survivorship bias**: Backtesting on current FAANG stocks ignores delisted/merged companies.
3. **Ignoring commissions**: Even with $0 commission brokers, slippage and spread matter for scalping.
4. **Correlated positions**: 2 positions in highly correlated stocks (e.g., AAPL and MSFT) is effectively 1 bet.
5. **Chasing performance**: A strategy that worked last month may not work next month.
6. **Not verifying**: Always write tests for your strategy code. A bug in indicator calculation can silently lose money.

## References

- `references/schwab-api.md` — Schwab API endpoints, auth flow, and code patterns
- `scripts/verify_strategy.py` — Reusable template for ad-hoc verification of trading strategy code
