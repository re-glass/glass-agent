# Schwab API Reference

## Authentication

### OAuth2 Flow
1. Redirect user to: `https://api.schwabapi.com/v1/oauth/authorize?client_id=KEY&redirect_uri=URI&response_type=code`
2. User logs in, gets redirected with `?code=AUTH_CODE&session=SESSION`
3. Exchange code for tokens: POST `/v1/oauth/token` with grant_type=authorization_code
4. Use access_token in Authorization: Bearer header
5. Refresh with grant_type=refresh_token when expired

### Personal Access Token (PAT)
- Generate at https://github.com/settings/tokens (for GitHub operations)
- For Schwab: use OAuth2 flow above
- PAT alternative: `curl -H "Authorization: token PAT" https://api.github.com/user`

## Key Endpoints

### Account Info
- `GET /v1/accounts/accountNumbers` — List account IDs
- `GET /v1/accounts/{accountId}` — Account details, balances, positions

### Market Data
- `GET /v1/marketdata/{symbol}/quotes` — Current quote (bid, ask, last)
- `GET /v1/marketdata/{symbol}/pricehistory` — Historical bars
  - Parameters: periodType (day/month/year), period (1-10), frequencyType (minute/daily), frequency (1/5/15/30)

### Orders
- `POST /v1/accounts/{accountId}/orders` — Place order
- `GET /v1/accounts/{accountId}/orders` — List orders

### Order Structure
```json
{
  "session": "NORMAL",
  "duration": "DAY",
  "orderType": "MARKET",
  "quantity": 10,
  "symbol": "AAPL",
  "instruction": "BUY"
}
```

## Rate Limits
- ~120 requests/minute for most endpoints
- Market data may have different limits
- Check response headers: X-RateLimit-Limit, X-RateLimit-Remaining

## Common Issues

### HTTPS Redirect Issue
- Local HTTP server (`http://127.0.0.1:8080`) CANNOT capture HTTPS redirects from Schwab's portal
- When user sets redirect URI to `https://127.0.0.1:8080`, browser shows "connection refused"
- **Solution**: Bot must have manual code entry fallback when `_capture_oauth_code()` returns None
- User copies `code=XXXX&session=YYYY` from browser URL and pastes into terminal

### Authorization Code Parsing
- Codes arrive in browser URL as: `?code=LONG_CODE&session=SESSION_ID`
- **Always parse**: split on `&` and use only the code portion
- **Test for this**: `code.split('&')[0]` handles both raw code and URL parameters
- Codes are single-use and expire in minutes — prompt user immediately after redirect

### Market Data Approval Delay
- After Schwab app approval, market data access may take hours or days to activate
- 404 errors on quotes/pricehistory endpoints = market data not yet active
- No fix — just wait. Check Schwab developer dashboard for approval status.

### Token Expiry
- Access tokens expire in ~30 minutes
- Refresh tokens last longer (typically 7 days)
- Always check token_expiry before API calls and refresh if needed

## Critical Pitfalls Discovered

### 1. API Base URL Structure
Schwab uses **three different base URLs**. Using the wrong one causes 404 errors:

| Category | Base URL |
|----------|----------|
| OAuth | `https://api.schwabapi.com/v1/oauth/...` |
| Trader (accounts, orders) | `https://api.schwabapi.com/trader/v1/...` |
| Market Data | `https://api.schwabapi.com/marketdata/v1/...` |

**Wrong**: `self.base_url = 'https://api.schwabapi.com/v1'` then `f'{base_url}/marketdata/{symbol}'` → 404

**Correct**: Define all three URLs explicitly.

### 2. Account ID: hashValue vs accountNumber
The `/accounts/accountNumbers` returns both `accountNumber` and `hashValue`. The hashValue is required for subsequent API calls. Using `accountNumber` causes 400 "Invalid account number".

### 3. Futures Quotes Don't Work
Futures symbols like `/YM` work for price history but NOT for quotes endpoint. Use price history to get latest prices for futures.

### 4. Quote Data Nesting
Live prices are at `quote.lastPrice`, not `ticker_data.lastPrice`. Always check `quote` first, then `extended` as fallback.

### 5. yfinance vs Schwab Symbol Format
- Schwab: `/YM`, `/GC` (slash prefix)
- yfinance: `YM=F`, `GC=F` (equals F suffix)

### 6. Status Line Scope Bug
When printing status for tickers NOT in positions, don't reference `pos` variable — it's only defined inside the positions loop. Use separate price fetching for status display.

### HTTPS Redirect
- Local HTTP server can't capture HTTPS redirects
- User must manually copy code from browser URL
- Fallback to manual input when _capture_oauth_code() returns None
