# Charles Schwab API Setup

## Overview

Schwab provides an official REST API for trading, market data, and account management. It requires OAuth2 authentication with a developer account.

## Registration Process

1. **Go to**: https://developer.schwab.com/
2. **Log in** with your Charles Schwab account
3. **Create New App**
   - Name: anything (e.g., "Scalping Bot")
   - Redirect URI: `http://localhost:8080` (for personal use)
   - Description: optional
4. **Save credentials**:
   - **App Key** (Client ID): public identifier
   - **App Secret** (Client Secret): keep private

## OAuth2 Flow

### Authorization URL
```
https://api.schwabapi.com/v1/oauth/authorize
  ?client_id=<APP_KEY>
  &redirect_uri=http%3A%2F%2Flocalhost%3A8080
  &response_type=code
```

### Exchange Code for Tokens
```python
response = requests.post(
    'https://api.schwabapi.com/v1/oauth/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'grant_type': 'authorization_code',
        'code': '<AUTH_CODE_FROM_REDIRECT>',
        'client_id': '<APP_KEY>',
        'client_secret': '<APP_SECRET>',
        'redirect_uri': 'http://localhost:8080',
    }
)
```

### Response
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 1800,
  "scope": "...",
  "token_type": "Bearer"
}
```

### Refresh Tokens
Access tokens expire in 30 minutes. Use the refresh token to get new ones:
```python
response = requests.post(
    'https://api.schwabapi.com/v1/oauth/token',
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    data={
        'grant_type': 'refresh_token',
        'refresh_token': '<REFRESH_TOKEN>',
        'client_id': '<APP_KEY>',
        'client_secret': '<APP_SECRET>',
    }
)
```

## Token Management Best Practices

1. **Save tokens to local file** (`tokens.json`) for persistence across sessions
2. **Auto-refresh** when `expires_in` is reached
3. **Never commit** tokens to version control
4. **Use file permissions** to restrict access (`chmod 600 tokens.json`)

## API Endpoints (Key)

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/accounts/accountNumbers` | Get account IDs |
| `GET /v1/accounts/{id}` | Account details & balances |
| `GET /v1/marketdata/{symbol}/pricehistory` | Historical price data |
| `GET /v1/marketdata/{symbol}/quotes` | Real-time quotes |
| `POST /v1/accounts/{id}/orders` | Place an order |
| `GET /v1/accounts/{id}/orders` | List orders |

## Paper Trading

Schwab supports paper trading accounts. Before going live:
1. Request paper trading access (or use your broker's paper trading feature)
2. Set `paper_trading: True` in your bot config
3. Validate all logic with fake money
4. Monitor for 2-4 weeks minimum

## Rate Limits

- Typically 120 requests/minute
- Check official docs for current limits
- Don't poll faster than necessary (30-60 second intervals recommended for scalping)

## Error Handling

Common error codes:
- `401 Unauthorized` → Token expired, refresh
- `403 Forbidden` → Invalid credentials or rate limited
- `404 Not Found` → Invalid symbol or endpoint
- `429 Too Many Requests` → Rate limit hit, back off

## Sample Code Structure

```python
# Authentication
schwab = SchwabAPI(config)
if not schwab.is_authenticated():
    schwab.authenticate()  # Opens browser for OAuth

# Get account
account_id = schwab.get_account_id()
account = schwab.get_account_info()

# Place order (market buy)
schwab.place_order('AAPL', 'BUY', quantity=10, order_type='MARKET')

# Get price history
history = schwwab.get_price_history('AAPL', period_type='day', period=5, frequency_type='minute', frequency=1)
```

## Live Trading Checklist

- [ ] OAuth2 tokens saved and working
- [ ] Account ID retrieved successfully
- [ ] Paper trading mode enabled
- [ ] Market hours check implemented (9:30 AM - 4:00 PM ET)
- [ ] Daily loss limit (kill switch) tested
- [ ] Max positions limit enforced
- [ ] Position sizing math verified
- [ ] Stop loss / take profit logic tested
- [ ] Market close position close verified
- [ ] Error handling for API failures
- [ ] 2+ weeks of paper trading completed

## Security Notes

- **Never share** App Secret or tokens
- Use environment variables or encrypted storage for production
- Rotate credentials if compromised
- Schwab API uses industry-standard OAuth2 — same security model as Google/Facebook APIs
