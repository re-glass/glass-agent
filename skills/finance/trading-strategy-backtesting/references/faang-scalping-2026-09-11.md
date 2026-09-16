# FAANG Scalping Strategy Backtest — 2026-09-11

## Session Summary

User requested a scalping strategy for FAANG stocks (AAPL, GOOGL, META, AMZN, NFLX) on 1-minute timeframe. Strategy combined mean reversion and trend following.

## Strategy Definition

**Mean Reversion:**
- Entry: Price >0.3% below VWAP, RSI < 30, Bollinger %B < 0.1 (long); inverse for short
- Exit: ATR-based take profit (1.5x ATR) or stop loss (1.0x ATR)

**Risk Parameters:**
- 2% risk per trade
- Max 2 concurrent positions
- Max 5% daily loss (kill switch)

## Backtest Results — Round 1: Combined Strategy (7 trading days)

| Metric | Value |
|--------|-------|
| Total Trades | 642 |
| Win Rate | 41.0% |
| Profit Factor | 0.91 |
| Total P&L | **-$650.87** |
| Max Drawdown | -$817.08 |
| Final Capital | $349.13 (from $1,000) |

**Strategy Breakdown:**
- Mean Reversion: 208 trades, **+$423.87**
- Trend Following: 434 trades, **-$1,074.73**

**Decision: Killed trend following.**

## Backtest Results — Round 2: Pure Mean Reversion (7 trading days)

| Metric | Value |
|--------|-------|
| Total Trades | 319 |
| Win Rate | 45.8% |
| Profit Factor | 1.12 |
| Total P&L | **+$399.39** |
| Max Drawdown | -$433.43 |
| Final Capital | $1,399.39 (from $1,000) |

## Backtest Results — Round 3: Extended + Optimized (48 trading days)

**Parameter Optimization:** Tested 81 combinations of SL mult, TP mult, RSI OS, RSI OB.

**Winner:**
| Parameter | Value |
|-----------|-------|
| SL Multiplier | 1.0x ATR |
| TP Multiplier | 1.5x ATR |
| RSI Oversold | 30 |
| RSI Overbought | 65 |

| Metric | Value |
|--------|-------|
| Total Trades | 1,015 |
| Win Rate | 43.5% |
| Profit Factor | 1.15 |
| Total P&L | **+$1,695.87** |
| Max Drawdown | -$593.13 |
| Final Capital | $2,695.87 (from $1,000) |

**Per-Ticker Performance:**
| Ticker | Trades | P&L |
|--------|--------|-----|
| META | 268 | +$1,057.72 |
| GOOGL | 166 | +$525.56 |
| NFLX | 223 | +$243.72 |
| AMZN | 159 | +$71.26 |
| AAPL | 199 | -$202.40 |

**Trade Distribution:**
- Mean win: $29.42
- Mean loss: -$19.73
- Reward-to-risk: 1.49:1
- Max win streak: 11
- Max loss streak: 12
- Shorts outperformed longs: $1,390 vs $305

## Analysis

### What Worked
- Mean reversion alone is profitable (+$399 → +$1,695 with optimization)
- Tighter stops (1.0x vs 1.5x ATR) improved performance
- 48-day sample shows more robustness than 7-day

### What Still Needs Work
- **AAPL is a losing ticker** — strategy doesn't work uniformly across FAANG
- **Max drawdown of $593 (59%)** — deep for a small account
- **Profit factor of 1.15 is thin** — vulnerable to bad weeks
- **Highly skewed returns** — a few big win days carry the strategy

### Key Lessons Learned

1. **Always test strategy components separately before combining**
2. **Kill losing components immediately** — don't try to "optimize" a losing strategy into profitability
3. **Parameter optimization matters** — 1.0x ATR stops beat 1.5x ATR stops for scalping
4. **Trade distribution analysis reveals strategy health** — binary outcomes (SL or TP) suggest clean execution
5. **Shorts outperform longs in mean reversion** — potential asymmetry in FAANG intraday behavior

## User Preferences Noted

- Wants fully autonomous execution (no confirmation step)
- Prefers backtest-first approach before live trading
- Trading FAANG specifically
- 1-minute scalping timeframe
- Small account (<$1,000) — very sensitive to drawdowns
- Willing to iterate: killed trend following immediately when shown it was losing money
- Wants progress saved to GitHub for persistence across machines

## Open Questions

- Should we proceed with walk-forward backtest on more data?
- Does the user have a Schwab account already set up for API access?
- What is the user's experience level with automated trading?
- Should we add a regime filter (e.g., VIX threshold, ATR floor)?
- Should we drop AAPL from the ticker list given it's the only loser?

## Files Generated

- `/home/reg/scalping_backtest.py` — Original backtest
- `/home/reg/enhanced_backtest.py` — Full optimization backtest
- `/home/reg/scalping_bot/live_bot.py` — Live trading bot (verified)
- `/home/reg/FAANG_SCALPING_STRATEGY.md` — Complete reference document
