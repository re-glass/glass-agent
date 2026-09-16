# Futures Bot Implementation Notes

Key lessons learned from building a futures mean reversion bot on Schwab API.

## Bug Fixes Session

### 1. `pos` Reference Outside Scope
**Problem:** Status line referenced `pos` outside the `paper_positions` loop.
```python
# WRONG
if last_price is None:
    last_price = pos['entry']  # pos not defined here
```

**Fix:**
```python
if last_price is not None:
    status += f"{ticker}:${last_price:.0f} "
else:
    status += f"{ticker}:? "
```

### 2. Futures Symbol Format
**Problem:** Used `YM=F` format which doesn't work with Schwab API price history.
**Fix:** Use `/YM`, `/GC`, `/ES` format (without `=F`).

### 3. Futures Quotes Return 404
**Problem:** Tested 10+ symbol formats for futures quotes — all returned 404.
**Solution:** Created `get_latest_price()` method that uses price history endpoint instead.

### 4. Stale vs Live Prices
**Problem:** `extended.lastPrice` is stale/delayed data (NFLX showed $77.78 vs actual ~$77.33).
**Fix:** Always use `quote.lastPrice`, not `extended.lastPrice`.

### 5. Auth Code with Session Parameter
**Problem:** User pasted full redirect URL with `&session=...` appended to code.
**Fix:** Strip session parameter before exchanging code.

## Verified Architecture

| Component | Base URL |
|-----------|----------|
| OAuth | `https://api.schwabapi.com/v1/oauth/...` |
| Trader | `https://api.schwabapi.com/trader/v1/...` |
| Market Data | `https://api.schwabapi.com/marketdata/v1/...` |

## Position Sizing for Futures

```python
CONTRACT_MULTIPLIERS = {
    '/YM': 5,      # $5 per point
    '/ES': 50,     # $50 per point
    '/NQ': 20,     # $20 per point
    '/CL': 1000,   # $1000 per point
    '/GC': 100,    # $100 per point
    '/SI': 5000,   # $5000 per point
}

multiplier = CONTRACT_MULTIPLIERS.get(ticker, 1)
point_risk = atr * multiplier
qty = max(1, int(risk_amount / point_risk))
```

## Multi-Strategy Backtest Results (7 days)

| Strategy | Best Market | P&L | PF | Win% |
|----------|-------------|-----|-----|------|
| Mean Reversion | YM=F | $1,149.79 | 2.68 | 61.3% |
| Trend Following | GC=F | $997.31 | 1.41 | 50.7% |
| Swing | GC=F | $417.47 | 1.23 | 46.7% |

## Backtest Period Limits

yfinance 1m data limit: ~8 days max per request.
For longer backtests, fetch in chunks and concatenate.
