# Schwab Trader API Endpoint Reference (Verified)

## Base URLs

| Purpose | Base URL | Note |
|---------|----------|------|
| OAuth, Accounts, Orders | `https://api.schwabapi.com/trader/v1` | NOT `/v1` — common mistake |
| Market Data | `https://api.schwabapi.com/marketdata/v1` | NOT `/v1/marketdata` — common mistake |

## Market Data Endpoints (under /marketdata/v1)

### Quotes (symbol in PATH)
```
GET /marketdata/v1/{symbol}/quotes
```

Sample response:
```json
{
  "AAPL": {
    "assetMainType": "EQUITY",
    "assetSubType": "COE",
    "quoteType": "NBBO",
    "realtime": true,
    "symbol": "AAPL",
    "bidPrice": 150.00,
    "askPrice": 150.05,
    "lastPrice": 150.02,
    "bidSize": 100,
    "askSize": 200
  }
}
```

### Price History (symbol as QUERY PARAM)
```
GET /marketdata/v1/pricehistory?symbol=AAPL&periodType=day&period=1&frequencyType=minute&frequency=1
```

**Critical:** Unlike quotes, price history takes `symbol` as a query parameter, not a path parameter.

Parameters:
- `periodType`: `day`, `month`, `year`, `ytd`
- `period`: `1`, `5`, `10`, `20`, `30`, `60`
- `frequencyType`: `minute`, `daily`, `weekly`, `monthly`
- `frequency`: `1`, `5`, `10`, `15`, `30` (for minute), `1` (for daily/weekly/monthly)

Sample response:
```json
{
  "candles": [
    {
      "datetime": 1789383600000,
      "open": 332.55,
      "high": 332.74,
      "low": 332.50,
      "close": 332.50,
      "volume": 8600
    }
  ],
  "symbol": "AAPL",
  "empty": false
}
```

## Account & Trading Endpoints (under /trader/v1)

### Get Account Numbers
```
GET /trader/v1/accounts/accountNumbers
```

Response:
```json
[
  {
    "accountNumber": "123456789",
    "hashValue": "abc123..."
  }
]
```

### Get Account Info
```
GET /trader/v1/accounts/{accountId}?fields=positions
```

### Place Order
```
POST /trader/v1/accounts/{accountId}/orders
```

Body:
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

For LIMIT orders add: `"price": 150.00`

### Get Orders
```
GET /trader/v1/accounts/{accountId}/orders
```

## OAuth Endpoints (under /v1 — NOT /trader/v1)

### Authorization URL (browser redirect)
```
GET /v1/oauth/authorize?client_id=XXX&redirect_uri=XXX&response_type=code
```

### Exchange Code for Tokens (POST)
```
POST /v1/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=XXX&client_id=XXX&client_secret=XXX&redirect_uri=XXX
```

### Refresh Token
```
POST /v1/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=XXX&client_id=XXX&client_secret=XXX
```

## Token Format

Access tokens are 76-character strings:
```
I0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.1ZpTga31YE3fReDVFB4xk10VVCOLwLIMGmHkomqlQe4@
```

Authorization codes may include `&session=...` suffix — strip before use.

## Error Handling

- `200`: Success
- `201`: Order created
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (bad/expired token)
- `404`: Endpoint not found — **check base URL (common mistake)**
- `429`: Rate limit exceeded
- `500`: Server error

## Rate Limits

- Standard: ~120 requests/minute
- Check `X-RateLimit-*` headers for actual limits
- Quote + price history per ticker per signal: 3 calls
- Position monitoring: 1 quote per position per 30 seconds
- Typical load: 15-20 calls/min for 5 tickers
