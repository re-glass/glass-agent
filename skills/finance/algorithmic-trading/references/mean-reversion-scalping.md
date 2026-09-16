# Mean Reversion Scalping Strategy

## Overview

A scalping strategy for FAANG stocks using mean reversion on 1-minute bars. Optimized via 48-day backtest with 81-parameter grid search.

## Strategy Rules

### Entry Conditions (ALL must be met)

**LONG:**
1. Price deviation from VWAP < -0.3% (price below VWAP)
2. RSI (14) < 30 (oversold)
3. Bollinger Bands (20, 2) %B < 0.1 (price near lower band)

**SHORT:**
1. Price deviation from VWAP > +0.3% (price above VWAP)
2. RSI (14) > 65 (overbought)
3. Bollinger Bands (20, 2) %B > 0.9 (price near upper band)

### Exit Rules
- **Stop Loss:** Entry ± (1.0 × ATR)
- **Take Profit:** Entry ± (1.5 × ATR)
- **Market Close:** All positions closed at 3:59 PM ET

### Position Sizing
```
risk_amount = account_value × 0.02
stop_distance = ATR × 1.0
qty = max(1, int(risk_amount / stop_distance))
```

## Optimized Parameters

| Parameter | Default | Optimized |
|-----------|---------|-----------|
| SL Multiplier | 1.5 | **1.0** |
| TP Multiplier | 2.0 | **1.5** |
| RSI Oversold | 30 | **30** |
| RSI Overbought | 70 | **65** |
| BB Period | 20 | **20** |
| BB Std Dev | 2.0 | **2.0** |

## Backtest Results (48 days, 1,015 trades)

| Metric | Value |
|--------|-------|
| Total P&L | +$1,695.87 |
| Win Rate | 43.5% |
| Profit Factor | 1.15 |
| Max Drawdown | -$593.13 |
## Session Results (Sept 2026)

### FAANG Stocks (7 days, 1m bars)
| Ticker | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| META | 268 | 45.8% | +$1,057.72 | - |
| GOOGL | 166 | - | +$525.56 | - |
| NFLX | 223 | - | +$243.72 | - |
| AMZN | 159 | - | +$71.26 | - |
| AAPL | 199 | - | -$202.40 | - |

### Futures (7 days, 1m bars) — Extended Session
| Ticker | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| YM=F | 49 | 38.8% | +$105.39 | 1.20 |
| CL=F | 212 | 42.0% | +$208.40 | 1.08 |
| SI=F | 114 | 49.1% | +$519.97 | 1.45 |
| GC=F | 53 | 32.1% | -$195.55 | 0.71 |

## Multi-Strategy Results (7 days)

| Strategy | Best Market | P&L | PF | Win% |
|----------|-------------|-----|-----|------|
| Mean Reversion | YM=F | $1,149.79 | 2.68 | 61.3% |
| Trend Following | GC=F | $997.31 | 1.41 | 50.7% |
| Swing | GC=F | $417.47 | 1.23 | 46.7% |

## Futures Trading Notes

- **Symbol format**: Use `/YM`, `/GC`, `/ES` for Schwab API (not `YM=F`)
- **Quotes don't work**: Futures quotes return 404 — use price history for all price data
- **Live vs stale**: Always use `quote.lastPrice`, not `extended.lastPrice`
- **No PDT rule**: Futures aren't subject to pattern day trading restrictions
- **24-hour trading**: Futures trade nearly 24/7 — no market hours filter needed

**Key insight:** AAPL was the only losing ticker. Consider dropping it.

### Trade Distribution
- **Binary outcomes:** Trades cluster near SL (-$20) and TP (+$30) — systematic execution
- **Shorts outperformed longs:** $1,390 vs $305
- **Max win streak:** 11 | **Max loss streak:** 12

## Risk Management

| Parameter | Value |
|-----------|-------|
| Risk per trade | 2% |
| Max daily loss | 5% (kill switch) |
| Max positions | 2 |
| Market hours | 9:30 AM - 4:00 PM ET |

## Implementation Notes

### Indicators
- **VWAP:** Daily reset, computed as cumulative(Volume × TypicalPrice) / cumulative(Volume)
- **Bollinger Bands:** 20-period SMA ± 2 standard deviations
- **RSI:** 14-period Wilder's smoothing
- **ATR:** 14-period true range

### Signal Timing
- Check every 30 seconds during market hours
- Only enter when all 3 conditions align
- Close all positions at 3:59 PM (no overnight holds)

### Common Pitfalls
1. **Trend following doesn't mix with mean reversion** — adding trend following turned a +$400 strategy into a -$650 loser
2. **Tighter stops work better for scalping** — 1.0x ATR outperformed 1.5x and 2.0x
3. **FAANG stocks are correlated** — 2 positions often = 1 effective bet
4. **AAPL behaves differently** — it was the only losing ticker in the universe

## Verification Checklist

Before live trading:
- [ ] All 6 ad-hoc tests pass (indicators, signals, sizing, loss limit, market hours, SL/TP)
- [ ] Paper traded for 2-4 weeks
- [ ] Daily loss limit tested and working
- [ ] Position sizing verified with current account balance
- [ ] Market hours filter confirmed (no pre/post-market trades)
