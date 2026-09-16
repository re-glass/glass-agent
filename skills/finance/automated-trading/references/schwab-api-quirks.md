# Schwab API Quirks & Debugging

## Common Issues

### 404 on All Endpoints (Including Account Info)

**Symptom:** `accountNumbers`, `quotes`, `pricehistory` all return 404 with no body.

**Causes:**
1. Market data access not yet approved (24-48h delay)
2. Token issued before full scope approval
3. Account not eligible for API trading

**Fixes:**
1. Re-authenticate to get fresh token: `rm tokens.json && python live_bot.py`
2. Wait 24-48 hours after app approval
3. Check schwab.com account for pending market data agreements

### OAuth Redirect Fails (127.0.0.1 refused)

**Cause:** Schwab redirects to HTTPS but local server is HTTP.

**Fix:** Use manual code entry. Bot will prompt:
```
Enter the authorization code: [paste code from browser URL]
```

**Code parsing:** Bot handles these formats:
- `ABC123` (just code)
- `https://localhost:8080/?code=ABC123&session=...` (full URL)
- `ABC123&session=...` (code with trailing params)

### Token Refresh Fails (401)

**Cause:** Refresh token expired (typically 7 days of inactivity).

**Fix:** Re-authenticate: `rm tokens.json && python live_bot.py`

### Rate Limits

**Default:** ~120 requests/minute.

**Bot calls per minute (5 tickers, 30s loop):**
- 5 quotes (for signals)
- 5 price histories (for indicators)
- 5 quotes (for exit monitoring)
- 1 account info (every signal)

**Optimization:** Cache account info, don't call every tick.

## App Setup Checklist

1. Create app at https://developer.schwab.com/
2. Redirect URI: `http://localhost:8080` (or `https://127.0.0.1:8080`)
3. Request scopes: `MarketData` + `AccountsAndTrading`
4. Set order limit (50-100/day for small accounts)
5. Wait for "Ready for Use" status
6. Re-authenticate after approval (fresh token)

## Testing Access Manually

```bash
curl -s -H "Bearer TOKEN" "https://api.schwabapi.com/v1/accounts/accountNumbers"
curl -s -H "Bearer TOKEN" "https://api.schwabapi.com/v1/marketdata/AAPL/quotes"
```

404 = not approved yet. 200 = ready to go.
