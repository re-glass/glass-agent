---
name: trading-strategy-backtesting
description: Build, backtest, and evaluate quantitative trading strategies. Covers data fetching, indicator computation, signal generation, risk management, position sizing, and performance analysis for stocks/ETFs.
---

# Trading Strategy Backtesting

This skill covers the end-to-end workflow for developing and validating quantitative trading strategies before live execution.

## When to Use

- User wants to build a trading strategy (mean reversion, trend following, momentum, scalping, etc.)
- User wants to backtest a strategy against historical data
- User needs to evaluate strategy performance (win rate, profit factor, drawdown, Sharpe ratio)
- User is setting up risk management rules (position sizing, stop loss, take profit, max daily loss)
- User wants to transition from backtesting to live trading
- User wants to connect to a broker API for live or paper trading

## Key Rules & Context

### Regulatory Environment (US Markets)
- **PDT Rule Repealed**: FINRA's Pattern Day Trader rule was repealed effective June 4, 2026. The $25,000 minimum equity requirement and 3-day-trades-per-5-days limit no longer apply. Brokers have until October 20, 2027 to fully implement new intraday margin standards.
- **T+1 Settlement**: Cash accounts still have T+1 settlement. Margin accounts have intraday margin requirements under the new rules.
- **Always verify current regulations** with FINRA/SEC before making trading decisions.

### Data Storage (GitHub)
When saving trading bot code to GitHub:
- Use **classic Personal Access Tokens** (fine-grained tokens fail on repo creation)
- `tokens.json`, `.env`, and `*.csv` are in `.gitignore` by default
- See `references/github-pat-auth.md` for auth troubleshooting

### Data Fetching (yfinance)
- **1-minute data limit**: yfinance limits 1-minute data to ~8 days per request. Use `Ticker.history(period='Nd', interval='1m')` instead of `yf.download()` for intraday data.
- **Multi-index columns**: yfinance may return MultiIndex columns. Flatten with `data.columns = data.columns.get_level_values(0)` if using `yf.download()`.
- **Timezone handling**: yfinance returns timezone-aware timestamps. Use `df.index = df.index.tz_localize(None)` for easier grouping.
- **VWAP computation**: For intraday VWAP, group by date and compute cumulative volume and volume-price.
- **API quirk**: `Ticker.history()` works for 1m data; `yf.download()` with start/end fails on ranges >30 days.

### Strategy Components

**Mean Reversion**
- Entry: Price extended from mean (VWAP, Bollinger Bands, RSI extremes)
- Exit: Price returns to mean or hits profit target
- Risk: Mean reversion fails in strong trends
- **Key insight from 2026-09-11 session**: Mean reversion alone was profitable on FAANG 1-min scalping (+$399 over 7 days)

**Trend Following**
- Entry: Trend confirmed (EMA crossovers, higher highs/lows), enter on pullback
- Exit: Trend reversal or trailing stop
- Risk: Whipsaws in ranging markets, many small losses
- **Key insight from 2026-09-11 session**: Trend following on 1-min FAANG stocks lost $1,074 over 7 days — whipsawed constantly in low-volatility intraday regimes

**Combined Strategies — CRITICAL LESSON**
- **ALWAYS test each strategy component separately before combining**
- If one component is profitable and one is losing, remove the losing one first
- Combining a profitable strategy with a losing one drags down overall performance
- Trend following and mean reversion are naturally conflicting (counter-trend vs. with-trend)
- On 1-minute timeframes, trend following tends to whipsaw on large-cap stocks (FAANG)
- **Correlation warning**: Trading the same highly correlated instruments (e.g., FAANG) with multiple strategies effectively doubles exposure without diversification

### Risk Management Framework
- **Position sizing**: Risk fixed % of account per trade (1-2% standard). Size = (Account × Risk%) / Stop Distance
- **Stop loss**: Technical level or ATR-based (1.5x-2x ATR common for scalping)
- **Take profit**: Reward-to-risk ratio (1:1 to 2:1 common)
- **Max daily loss**: Kill switch at X% drawdown (user-defined)
- **Max positions**: Limit concurrent positions to avoid overconcentration

### Backtesting Best Practices
- **Sample size**: Minimum 3-6 months of data for statistical significance. 1-2 weeks is insufficient for conclusive results.
- **Walk-forward testing**: Validate on out-of-sample data
- **Slippage & commissions**: Include realistic transaction costs (often $0 for modern brokers but slippage matters for scalping)
- **Overfitting**: Avoid excessive parameter optimization — simple, robust rules beat complex fitted curves
- **Correlated instruments**: Trading 5 tech stocks simultaneously is not 5 independent bets

### Performance Metrics
- **Win rate**: % of profitable trades (not meaningful alone)
- **Profit factor**: Gross profits / Gross losses (>1.0 is breakeven after costs)
- **Max drawdown**: Largest peak-to-trough decline
- **Sharpe ratio**: Risk-adjusted return
- **Expectancy**: Average P&L per trade

## Common Pitfalls

1. **Ignoring correlation**: Trading multiple highly correlated stocks (FAANG) with multiple strategies = concentrated risk, not diversification
2. **Too many trades**: High frequency doesn't guarantee profit; overtrading increases noise and transaction costs
3. **Tight stops on volatile instruments**: ATR stops need room to breathe
4. **No regime filter**: Strategy that works in trends fails in ranges and vice versa
5. **Survivorship bias**: Testing only on current FAANG stocks ignores those that dropped out

## Live Trading Integration

### Broker Selection
| Broker | API | Status | Notes |
|--------|-----|--------|-------|
| **Charles Schwab** | Official REST API | ✅ **Recommended** | OAuth2, paper trading, no ToS risk |
| Robinhood | Reverse-engineered | ❌ Avoid | Violates ToS, account termination risk |

### Schwab API Setup
1. Sign up at https://developer.schwab.com/ with your Schwab account
2. Create an app → redirect URI: `http://localhost:8080`
3. Save App Key (Client ID) and App Secret (Client Secret)
4. OAuth2 flow: browser redirect → capture code → exchange for tokens
5. Tokens auto-refresh; save to local file for persistence

### Live Trading Workflow
1. Start with `paper_trading: True` in config
2. Use `Ticker.history()` for backtests (not for live — use streaming API in production)
3. In live mode, stream real-time bars or poll every 30-60 seconds
4. Implement daily P&L tracking — kill switch at max_daily_loss_pct
5. Market hours check (9:30 AM - 4:00 PM ET)
6. Close all positions at market close

### Live Bot Architecture
```
config (paper trading flag, API keys, risk params)
    ↓
OAuth2 authentication (tokens cached locally)
    ↓
Main loop (30-60 second intervals):
    ├── Market hours check
    ├── Daily loss limit check  
    ├── Close existing positions (SL/TP/MOC)
    ├── Fetch real-time data per ticker
    ├── Compute indicators (VWAP, BB, RSI, ATR)
    ├── Generate signals
    ├── Position sizing (2% risk)
    └── Place orders (if not paper trading)
```

### Production vs Backtest Differences
| Aspect | Backtest | Live |
|--------|----------|------|
| Data source | yfinance (historical) | Schwab streaming API |
| Execution | Instant at close | Real fills with slippage |
| Position tracking | In-memory list | API order status checks |
| Stop loss/take profit | Price-based exit | Native orders or price monitoring |
| Paper trading | N/A | Must test first! |

### Verification
- Always verify indicator calculations with a standalone test script
- Test position sizing math independently
- Test daily loss limit boundary conditions
- Test market hours logic (before/after hours)
- Verify BB_PctB CAN go outside [0,1] (don't assert otherwise)

## References

- `references/pdt-rule-change.md`: Details on the 2026 PDT repeal and new margin standards
- `references/faang-scalping-2026-09-11.md`: Session-specific backtest results and strategy analysis
- `references/yfinance-1m-data.md`: Workarounds for fetching 1-minute data with yfinance
- `references/schwab-api-setup.md`: Schwab API registration, OAuth2 flow, and token management
- `references/github-pat-auth.md`: GitHub authentication (PATs, classic vs fine-grained, troubleshooting)
- `templates/scalping-bot.py`: Complete live bot template (Schwab API, mean reversion, risk management)

## Verification

After backtesting, verify:
- Total trades > 100 for statistical relevance
- Profit factor > 1.0 (ideally > 1.2)
- Max drawdown < 20% of account
- Win rate is secondary to expectancy
- No single day or trade dominates results
- BB_PctB CAN go outside [0,1] — don't assert otherwise in tests
