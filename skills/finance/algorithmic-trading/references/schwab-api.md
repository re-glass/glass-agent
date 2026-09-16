# Schwab API Reference

## Base URL
`https://api.schwabapi.com/v1`

## Authentication

### OAuth2 Flow

1. **Get authorization code**: User logs in at `https://developer.schwab.com/`
2. **Exchange for tokens**: POST to `/oauth/token` with code
3. **Refresh tokens**: POST to `/oauth/token` with refresh_token grant

### Python Client Pattern

```python
class SchwabAPI:
    def __init__(self, config):
        self.base_url = 'https://api.schwabapi.com/v1'
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
    
    def authenticate(self):
        # Open browser for OAuth2
        auth_url = f"{self.base_url}/oauth/authorize?client_id={app_key}&redirect_uri={redirect_uri}&response_type=code"
        webbrowser.open(auth_url)
        # Capture callback code, exchange for tokens
    
    def refresh_tokens(self):
        # Refresh access token using refresh token
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data={'grant_type': 'refresh_token', 'refresh_token': self.refresh_token}
        )
        # Update tokens
    
    def get_headers(self):
        return {'Authorization': f'Bearer {self.access_token}'}
```

## Key Endpoints

### Account
- `GET /accounts/accountNumbers` — Get account IDs
- `GET /accounts/{account_id}` — Account details (balance, positions)

### Market Data
- `GET /marketdata/{symbol}/pricehistory` — Historical price data
- `GET /marketdata/{symbol}/quotes` — Current quote

### Orders
- `GET /accounts/{account_id}/orders` — List orders
- `POST /accounts/{account_id}/orders` — Place order

### Price History Parameters
- `periodType`: day, month, year, ytd
- `period`: number of periods (e.g., 5 for 5 days)
- `frequencyType`: minute, daily, weekly, monthly
- `frequency`: 1, 5, 10, 15, 30 (for minute data)

### Order Structure
```python
order = {
    'session': 'NORMAL',
    'duration': 'DAY',
    'orderType': 'MARKET',  # or 'LIMIT'
    'quantity': 10,
    'symbol': 'AAPL',
    'instruction': 'BUY',  # or 'SELL'
    # For LIMIT orders:
    'price': 150.50,
}
```

## Rate Limits
- Typically 120 requests/minute for market data
- Check current docs at https://developer.schwab.com/

## Common Issues

### 1-Minute Data Limitation
Schwab limits 1-minute data to recent periods only. For historical minute data, use multiple requests with different date ranges.

### Token Expiration
Access tokens expire in 30 minutes. Always check expiry and refresh if needed.

### Paper Trading
Schwab supports paper trading accounts. Use separate API credentials for paper vs live trading.
