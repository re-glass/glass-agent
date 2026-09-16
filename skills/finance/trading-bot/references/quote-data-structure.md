# Quote Data Structure (Schwab API)

## Quote Response Hierarchy

```
{
  "AAPL": {
    "quote": {
      "lastPrice": 333.68,        ← LIVE PRICE (use this)
      "bidPrice": 333.85,
      "askPrice": 333.91,
      "quoteTime": 1789569375337
    },
    "extended": {
      "lastPrice": 331.11,        ← STALE PRICE (fallback only)
      "quoteTime": 0
    },
    "regular": {
      "regularMarketLastPrice": 333.68  ← CROSS-CHECK
    }
  }
}
```

## Price Selection Logic

```python
# CORRECT — Live price with fallback
ticker_data = quote.get(ticker, {})
last_price = ticker_data.get('quote', {}).get('lastPrice', 0)
if last_price == 0:
    last_price = ticker_data.get('extended', {}).get('lastPrice', 0)

# WRONG — Uses stale data
last_price = quote[ticker].get('lastPrice', 0)  # May return extended.lastPrice
```

## Common Mistake

The `extended.lastPrice` field contains stale/delayed data. If you use `quote[ticker].get('lastPrice')` without specifying the `quote` sub-object, you may get the stale price (e.g., NFLX showing $77.78 when live is $77.55).

## Verification

To confirm live data is working:
1. Print prices every 30 seconds
2. Prices should change between iterations
3. If a price stays identical for many iterations, you may be reading stale data
4. Cross-check with `regular.regularMarketLastPrice` — should match `quote.lastPrice`
