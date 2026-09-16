# Futures Trading & Multi-Strategy Patterns

This reference covers futures-specific trading patterns and multi-strategy testing approaches.

## Futures vs Stocks

| Feature | Stocks | Futures |
|---------|--------|---------|
| Trading Hours | 6.5h/day | ~23h/day |
| PDT Rule | Repealed 2026 | N/A |
| Contract Sizes | 1 share = 1 unit | Varies ($5-$5000/point) |
| Quotes Endpoint | Works | Returns 404 |
| Symbol Format | AAPL | /YM, /GC, /ES (not YM=F) |
| Data Source | Schwab API | yfinance for backtest |

## Futures Symbol Formats

| Market | yfinance | Schwab API Price History |
|--------|----------|--------------------------|
| S&P 500 E-mini | ES=F | /ES |
| Nasdaq 100 E-mini | NQ=F | /NQ |
| Dow E-mini | YM=F | /YM |
| Crude Oil | CL=F | /CL |
| Gold | GC=F | /GC |
| Silver | SI=F | /SI |

## Contract Multipliers

```python
CONTRACT_MULTIPLIERS = {
    '/YM': 5,      # $5 per point
    '/ES': 50,     # $50 per point
    '/NQ': 20,     # $20 per point
    '/CL': 1000,   # $1000 per point
    '/GC': 100,    # $100 per point
    '/SI': 5000,   # $5000 per point
}
```

## Multi-Strategy Framework

### Strategy Interface
Each strategy is a function that takes a row of indicator data and returns:
- `1` = Long signal
- `-1` = Short signal
- `0` = No signal

### Strategy Types

**Mean Reversion (Scalping)**
- Entry: Price extended from VWAP + RSI extreme + BB touch
- Exit: 1.0x ATR stop, 1.5x ATR target
- Timeframe: 1-min bars
- Hold: Minutes to hours

**Trend Following (Breakout/Pullback)**
- Entry: EMA crossover + pullback to EMA in trend direction
- Exit: 1.5x ATR stop, 2.0x ATR target
- Timeframe: 1-min or 5-min bars
- Hold: Hours to 1 day

**Swing Trading (Multi-day)**
- Entry: Strong trend + RSI reset (40-60 range)
- Exit: Time-based (3 days) or wider ATR stops
- Timeframe: 1-hour bars
- Hold: 1-5 days

## Backtest Period Limits

| Source | 1m Data | 5m Data | 1h Data |
|--------|---------|---------|---------|
| yfinance | ~8 days | ~60 days | ~730 days |
| Schwab API | ~30 days | ~60 days | ~365 days |

## Live Data Verification

### Stale vs Live Prices
Schwab quote responses contain TWO prices:
- `extended.lastPrice` — STALE (snapshot/delayed)
- `quote.lastPrice` — LIVE (use this!)

Always use `quote.lastPrice` for trading decisions.

### Futures Quotes Don't Work
Futures quotes return 404 via Schwab API. Use price history endpoint instead:
```python
def get_latest_price(self, symbol):
    history = self.get_price_history(symbol, period_type='day', period=1, 
                                      frequency_type='minute', frequency=1)
    candles = history['candles']
    return candles[-1]['close']
```

## Session Results (Sept 2026)

### Mean Reversion (7 days, 1m bars)
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| SI=F | 114 | 49.1% | +$519.97 | 1.45 |
| CL=F | 212 | 42.0% | +$208.40 | 1.08 |
| YM=F | 49 | 38.8% | +$105.39 | 1.20 |

### Trend Following (7 days, 5m bars)
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| GC=F | 304 | 50.7% | +$997.31 | 1.41 |
| MSFT | 77 | 53.2% | +$351.04 | 1.51 |
| CL=F | 220 | 45.9% | +$308.93 | 1.13 |

### Swing (60 days, 1h bars)
| Market | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| GC=F | 135 | 46.7% | +$417.47 | 1.23 |
| CL=F | 153 | 46.4% | +$225.95 | 1.14 |
| TSLA | 54 | 51.9% | +$137.02 | 1.32 |

## Implementation Checklist

- [ ] Paper trading mode (`paper_trading: True`)
- [ ] Position tracking dict (`paper_positions`)
- [ ] SL/TP monitoring every tick
- [ ] Daily loss limit (dynamic, not hardcoded)
- [ ] Max positions enforcement
- [ ] Duplicate entry blocking per ticker
- [ ] Market close handling (or 24h loop for futures)
- [ ] Live price verification (`quote.lastPrice`)
- [ ] Futures: use `get_latest_price()` not `get_quote()`
