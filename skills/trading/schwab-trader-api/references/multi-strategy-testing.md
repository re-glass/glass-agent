# Multi-Strategy Testing & Live Data Verification

This reference covers testing multiple strategies across stocks and futures, plus verifying live data feeds.

## Strategy Definitions

### 1. Mean Reversion (Scalping)
**Entry:** Price extended from VWAP + RSI extreme + BB touch
**Exit:** 1.0x ATR stop, 1.5x ATR target
**Timeframe:** 1-min bars, close at end of day

### 2. Trend Following (Breakout/Pullback)
**Entry:** EMA crossover with pullback to EMA in trend direction
**Exit:** 1.5x ATR stop, 2.0x ATR target
**Timeframe:** 1-min or 5-min bars

### 3. Swing Trading (Multi-day)
**Entry:** Strong trend + RSI reset (40-60 range)
**Exit:** Time-based (3 days max) or wider ATR stops
**Timeframe:** 1-hour bars, hold 1-5 days

## Symbol Formats

| Market | yfinance | Schwab API | Contract Size |
|--------|----------|------------|---------------|
| S&P 500 E-mini | ES=F | /ES | $50/point |
| Nasdaq 100 E-mini | NQ=F | /NQ | $20/point |
| Dow E-mini | YM=F | /YM | $5/point |
| Crude Oil | CL=F | /CL | $1,000/point |
| Gold | GC=F | /GC | $100/point |
| Silver | SI=F | /SI | $5,000/point |

## Backtest Period Limits by Source

| Source | 1m Data Limit | 5m Data Limit | 1h Data Limit |
|--------|---------------|---------------|---------------|
| yfinance | ~8 days | ~60 days | ~730 days |
| Schwab API | ~30 days | ~60 days | ~365 days |

## Live Data Verification Checklist

1. **Prices updating?** — Status line should show different prices each loop
2. **No stale data?** — Compare `quote.lastPrice` vs `extended.lastPrice`
3. **All tickers working?** — No 404 errors in output
4. **Account info loading?** — Balance and buying power displayed

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| All prices $0 | Using `extended.lastPrice` | Switch to `quote.lastPrice` |
| Same price every tick | Cached token or stale data | Delete `tokens.json`, re-auth |
| 404 on quotes | Futures don't support quotes | Use `get_latest_price()` with price history |
| No trades generating | Market hours or signal threshold | Check time and indicator values |

## Multi-Strategy Backtest Script

Use `strategy_comparison.py` to test all 3 strategies across all markets in one run.

```bash
cd /home/reg/scalping_bot
source venv/bin/activate
python3 strategy_comparison.py
```

## Session Results (Sept 2026)

### Top Mean Reversion Performers
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| YM=F (Dow) | 49 | 38.8% | $105.39 | 1.20 |
| CL=F (Crude) | 212 | 42.0% | $208.40 | 1.08 |
| SI=F (Silver) | 114 | 49.1% | $519.97 | 1.45 |

### Top Trend Following Performers
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| GC=F (Gold) | 304 | 50.7% | $997.31 | 1.41 |
| MSFT | 77 | 53.2% | $351.04 | 1.51 |

### Top Swing Performers
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| GC=F (Gold) | 135 | 46.7% | $417.47 | 1.23 |
| CL=F (Crude) | 153 | 46.4% | $225.95 | 1.14 |
