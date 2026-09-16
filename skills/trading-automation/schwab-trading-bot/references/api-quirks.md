# Schwab API Quirks & Pitfalls

## Discovered During Bot Development (2026-09-15)

### 1. Account ID Issue
**Problem:** All account endpoints returned 400 "Invalid account number"
**Root Cause:** Using `accountNumber` from `/accounts/accountNumbers` response instead of `hashValue`
**Fix:** Use `accounts[0]['hashValue']` for all subsequent account calls

### 2. Futures Quotes Don't Work
**Problem:** `GET /marketdata/v1/{symbol}/quotes` returns 404 for futures
**Workaround:** Use `pricehistory` endpoint with `period=1, frequency=1` for latest price
**Code:**
```python
history = api.get_price_history('/YM', period_type='day', period=1, frequency_type='minute', frequency=1)
latest_close = history.iloc[-1]['Close']
```

### 3. Nested Price Fields
Quote response has multiple price locations:
- `quote.lastPrice` — **LIVE** (correct to use)
- `extended.lastPrice` — **STALE** (previous close or delayed)
- `regular.regularMarketLastPrice` — same as quote.lastPrice

**Always use `quote.lastPrice` for live trading decisions.**

### 4. Symbol Format Mismatches
| Context | Format |
|---------|--------|
| Schwab API | `/YM`, `/GC`, `/ES` |
| yfinance | `YM=F`, `GC=F`, `ES=F` |
| Schwab portal | `/YM` (with slash prefix) |

### 5. Datetime JSON Serialization
**Problem:** `positions.json` save fails with "Object of type datetime is not JSON serializable"
**Fix:** Convert `entry_time` to ISO string before saving, parse back on load

### 6. Signal Handling for Graceful Shutdown
**Problem:** Bot killed with Ctrl+C leaves orphaned positions
**Solution:** Register signal handlers that close all positions before exit
```python
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)
```

### 7. Futures Trading Hours
- Futures trade nearly 24/5 (nearly 24 hours/day, 5 days/week)
- No market hours restriction like stocks (9:30 AM - 4:00 PM ET)
- Can run bot continuously without "outside market hours" checks
