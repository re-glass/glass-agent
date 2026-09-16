# Schwab API Reference

## Overview
- **OAuth Base URL:** `https://api.schwabapi.com/v1/oauth/...`
- **Trader Base URL:** `https://api.schwabapi.com/trader/v1/...`
- **Market Data Base URL:** `https://api.schwabapi.com/marketdata/v1/...`
- **Auth:** OAuth2 (authorization code flow)
- **Docs:** https://developer.schwab.com/

## Authentication Flow

### 1. Create App
- Go to https://developer.schwab.com/
- Create app with redirect URI (e.g., `http://localhost:8080` or `https://127.0.0.1:8080`)
- Select scopes: `MarketData`, `AccountAccess`, `Trade`, `Orders`
- Save App Key (Client ID) and App Secret (Client Secret)

### 2. OAuth2 Authorization
```
GET /oauth/authorize?client_id={app_key}&redirect_uri={redirect_uri}&response_type=code
```
- User logs in to Schwab
- Browser redirects to `redirect_uri` with `?code=AUTH_CODE&session=...`
- **Note:** If using HTTPS redirect to localhost, the local server may not receive the callback. User must manually paste the code from the browser URL.

### 3. Exchange Code for Tokens
```
POST /oauth/token
Body: grant_type=authorization_code&code={code}&client_id={app_key}&client_secret={app_secret}&redirect_uri={redirect_uri}
```
Returns: `access_token`, `refresh_token`, `expires_in`

### 4. Refresh Tokens
```
POST /oauth/token
Body: grant_type=refresh_token&refresh_token={refresh_token}&client_id={app_key}&client_secret={app_secret}
```

## Key Endpoints

| Purpose | Method | Endpoint |
|---------|--------|----------|
| Get account numbers | GET | `/trader/v1/accounts/accountNumbers` |
| Get account info | GET | `/trader/v1/accounts/{hashValue}` |
| Get price history | GET | `/marketdata/v1/pricehistory?symbol={symbol}` |
| Get quote | GET | `/marketdata/v1/{symbol}/quotes` |
| Place order | POST | `/trader/v1/accounts/{hashValue}/orders` |
| Get orders | GET | `/trader/v1/accounts/{hashValue}/orders` |

## CRITICAL: Account Numbers

The account info endpoint requires the **hashValue**, NOT the plain account number:

```python
# WRONG — returns 400 "Invalid account number"
response = requests.get(f"{base}/trader/v1/accounts/{account_number}")

# CORRECT — use hashValue from accountNumbers endpoint
response = requests.get(f"{base}/trader/v1/accounts/{hash_value}")
```

The `accountNumbers` endpoint returns:
```json
[{"accountNumber": "56781519", "hashValue": "968DE78C99FF469850398683B7A40052F210137C15E21EC87668DAD3FEB1C898"}]
```

Save both — display `accountNumber` to user, use `hashValue` for API calls.

## Quote Data Structure

Quotes have THREE price locations — use the right one:

| Field | Path | Use Case |
|-------|------|----------|
| **Live price** | `quote.lastPrice` | Entry, SL/TP checks |
| Stale price | `extended.lastPrice` | Fallback only |
| Regular market | `regular.regularMarketLastPrice` | Cross-check |

**Never use `extended.lastPrice` as the primary price** — it's stale/delayed data.

Example quote response:
```json
{
  "AAPL": {
    "quote": {
      "lastPrice": 333.68,
      "bidPrice": 333.85,
      "askPrice": 333.91
    },
    "extended": {
      "lastPrice": 331.11
    },
    "regular": {
      "regularMarketLastPrice": 333.68
    }
  }
}
```

## Price History Parameters

Symbol is a **query parameter**, NOT a path parameter:
```
GET /marketdata/v1/pricehistory?symbol=AAPL&periodType=day&period=1&frequencyType=minute&frequency=1
```

- `periodType`: `day`, `month`, `year`, `ytd`
- `period`: number of periods (e.g., `1` for today)
- `frequencyType`: `minute`, `daily`, `weekly`, `monthly`
- `frequency`: `1`, `5`, `10`, `15`, `30` (minutes)

## Order Structure
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

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 on all endpoints | Wrong base URL | Use `/trader/v1` for accounts, `/marketdata/v1` for quotes |
| 400 "Invalid account number" | Using plain account number | Use `hashValue` from accountNumbers endpoint |
| Stale prices ($0 or wrong) | Using `extended.lastPrice` | Use `quote.lastPrice` for live data |
| Empty 404 body | Token lacks scopes | Re-authenticate, check app approval |
| Auth code parsing errors | Session parameter appended | Parse only `code=` value, strip `&session=` |
| Redirect fails | HTTPS to localhost | Use manual code paste fallback |

## Notes
- Rate limit: typically 120 requests/minute
- Paper trading may require separate account setup
- Market data access may take time to activate after app approval
- Always verify live data is flowing before going live (prices should change every 30s)
