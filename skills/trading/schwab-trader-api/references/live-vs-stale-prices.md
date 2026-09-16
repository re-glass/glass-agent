# Live vs Stale Prices in Schwab API

## Problem
Quote responses from `GET /marketdata/v1/{symbol}/quotes` contain multiple price fields at different nesting levels:

```json
{
  "extended": {
    "lastPrice": 77.78,      // ← STALE: snapshot, delayed, or pre-market
    "quoteTime": 0
  },
  "quote": {
    "lastPrice": 77.335,     // ← LIVE: real-time NBBO
    "bidPrice": 77.33,
    "askPrice": 77.34,
    "quoteTime": 1789569376690
  },
  "regular": {
    "regularMarketLastPrice": 77.335  // ← regular session
  }
}
```

## Impact
Using `extended.lastPrice` causes:
- Stale price displays (bot looks frozen)
- Trades based on old prices
- SL/TP triggers at wrong levels

## Fix
Always read from `quote.lastPrice` with `extended` as fallback:

```python
ticker_data = quote.get(ticker, {})
last_price = ticker_data.get('quote', {}).get('lastPrice', 0)
if last_price == 0:
    last_price = ticker_data.get('extended', {}).get('lastPrice', 0)
```

Same pattern for `bidPrice`/`askPrice` on order placement.

## Verification
If NFLX shows $77.78 (stale) instead of ~$449 (live), the fix is needed. Check by comparing bot display to any public quote source.
