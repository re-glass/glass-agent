---
name: trading-bot-dev
title: Automated Trading Bot Development
description: Build, test, and deploy automated trading bots with broker APIs (Schwab, etc.), backtesting, and risk management
triggers:
  - trading bot
  - automated trading
  - schwab api
  - backtesting
  - mean reversion
  - scalping
  - strategy optimization
---

# Automated Trading Bot Development

## Overview

Class-level skill for building automated trading systems: broker API integration, strategy backtesting, parameter optimization, and deployment workflows.

## Core Workflow

### 1. Strategy Definition
- Define entry/exit rules as computable conditions (indicators + thresholds)
- Specify risk parameters: per-trade risk, daily loss limit, max position count
- Choose timeframe and tickers/universe

### 2. Backtesting Framework
- Use `yfinance` for historical data (see `references/yfinance-data.md`)
- Implement walk-forward parameter optimization:
  - Grid search over parameter space
  - Track profit factor, win rate, max drawdown, daily P&L distribution
  - Analyze trade concentration (top N trades vs total P&L)
- Verify strategy produces clean, rule-based trade distribution

### 3. Broker API Integration
- Schwab: OAuth2 authentication (see `references/schwab-auth.md`)
- Implement indicator computation from streaming/quote data
- Position sizing: `qty = max(1, int(account_risk / stop_distance))`
- Daily loss limit as hard kill switch

### 4. Deployment
- Paper trade first (minimum 2-4 weeks)
- Monitor for: slippage, fills, API rate limits, indicator calculation drift
- Log all trades for post-hoc analysis

## Risk Management Rules

| Parameter | Conservative | Moderate |
|-----------|-------------|----------|
| Risk per trade | 1-2% | 2-3% |
| Daily loss limit | 3-5% | 5-8% |
| Max positions | 1-2 | 2-3 |
| Profit factor threshold | > 1.2 | > 1.1 |

## Common Pitfalls

- **PDT Rule**: Repealed June 2026 (FINRA replaced with intraday margin standards, phase-in until Oct 2027). No longer a $25k minimum equity requirement for day trading.
- **yfinance 1m limits**: Only ~8 days of 1m data per request. Use `Ticker.history()` not `yf.download()`.
- **Schwab redirect URI**: Portal may reject `localhost`. Use manual code fallback or placeholder URL.
- **Overfitting**: Profit factor < 1.2 or top 10 trades > 30% of total P&L suggests curve fitting.
- **Correlated positions**: Multiple positions on highly correlated tickers (e.g., FAANG) is effectively one bet.

## References

- `references/schwab-auth.md` — OAuth2 setup, PAT authentication, common issues
- `references/yfinance-data.md` — Data fetching patterns and workarounds
