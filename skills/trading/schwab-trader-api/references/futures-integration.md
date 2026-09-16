# Futures Integration via Schwab API

## Critical Finding: Futures Quotes NOT Supported

**Futures quotes return 404 via Schwab API.** This was tested extensively with multiple symbol formats:
- `/YM`, `/YM=F`, `YM=F`, `YM` — all return 404 for quotes endpoint
- But `/YM/pricehistory` works perfectly

**Workaround:** Use price history endpoint for everything — latest candle close = current price.

## Futures Symbol Format

| Context | Format | Example |
|---------|--------|---------|
| Price History API | `/YM`, `/GC`, `/ES` | `?symbol=/YM` |
| yfinance | `YM=F`, `GC=F`, `ES=F` | `yf.download('YM=F')` |
| Actual contract | Price history returns full symbol | `/YMZ26` (June 2026) |

## Available Futures

| Symbol | Market | Contract Size |
|--------|--------|---------------|
| `/YM` | Dow Jones E-mini | $5/point |
| `/ES` | S&P 500 E-mini | $50/point |
| `/NQ` | Nasdaq 100 E-mini | $20/point |
| `/CL` | Crude Oil | $1,000/point |
| `/GC` | Gold | $100/point |
| `/SI` | Silver | $5,000/point |

## Implementation: get_latest_price Method

Since futures quotes don't work, use price history for all price data:

```python
def get_latest_price(self, symbol):
    """Get latest price from most recent candle in price history."""
    history = self.get_price_history(symbol, period_type='day', period=1, 
                                      frequency_type='minute', frequency=1)
    if not history or 'candles' not in history or not history['candles']:
        return None, None, None
    
    candles = history['candles']
    latest = candles[-1]
    last_price = latest.get('close', 0)
    
    # Approximate bid/ask from recent candles
    if len(candles) >= 2:
        prev = candles[-2]
        bid = prev.get('close', last_price)
        ask = last_price
    else:
        bid = last_price
        ask = last_price
    
    return last_price, bid, ask
```

## Main Loop Adaptation

Replace all `api.get_quote(ticker)` calls with:
```python
last_price, bid, ask = api.get_latest_price(ticker)
if last_price is None:
    continue
```

This works for both stocks (where quotes work) and futures (where only price history works).

## Position Sizing for Futures

Futures require different position sizing due to contract multipliers:
```python
# Contract multipliers
CONTRACT_MULTIPLIERS = {
    '/YM': 5,      # $5 per point
    '/ES': 50,     # $50 per point
    '/NQ': 20,     # $20 per point
    '/CL': 1000,   # $1000 per point
    '/GC': 100,    # $100 per point
    '/SI': 5000,   # $5000 per point
}

# Risk-based position sizing for futures
multiplier = CONTRACT_MULTIPLIERS.get(ticker, 1)
point_risk = atr * multiplier  # Dollar risk per contract
qty = max(1, int(risk_amount / point_risk))
```

## Backtest Results (Mean Reversion, 7 days, 1m bars)

| Ticker | Trades | Win Rate | P&L | PF |
|--------|--------|----------|-----|-----|
| SI=F | 114 | 49.1% | +$519.97 | 1.45 |
| CL=F | 212 | 42.0% | +$208.40 | 1.08 |
| ES=F | 33 | 45.5% | +$103.43 | 1.32 |
| YM=F | 49 | 38.8% | +$105.39 | 1.20 |
| GC=F | 53 | 32.1% | -$195.55 | 0.71 |

## Multi-Strategy Results (7 days)

| Strategy | Best Market | P&L | PF | Win% |
|----------|-------------|-----|-----|------|
| Mean Reversion | YM=F | $1,149.79 | 2.68 | 61.3% |
| Trend Following | GC=F | $997.31 | 1.41 | 50.7% |
| Swing | GC=F | $417.47 | 1.23 | 46.7% |

## Key Differences from Stocks

1. **24-hour trading** — no market hours restriction, but forex-style sessions
2. **Higher volatility** — wider stops needed
3. **Contract rollover** — contracts expire, need to monitor
4. **No PDT rule** — futures aren't subject to pattern day trading
5. **Margin requirements** — intraday margin applies

## Session Notes

- Futures quotes endpoint may be added in future API updates
- Always fallback to price history for futures
- Test both `/YM` and `YM=F` formats for price history (yfinance uses latter)
