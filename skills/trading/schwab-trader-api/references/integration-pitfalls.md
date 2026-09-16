# Schwab API Integration Pitfalls (Session-Learned)

## 1. Three Base URLs (Critical — ALL must be correct)

| Purpose | Base URL | Common Wrong URL |
|---------|----------|------------------|
| **OAuth** (authorize, token) | `https://api.schwabapi.com/v1/oauth/...` | `https://api.schwabapi.com/trader/v1/oauth/...` ← WRONG |
| **Trader API** (Accounts, Orders) | `https://api.schwabapi.com/trader/v1/...` | `https://api.schwabapi.com/v1/...` ← WRONG |
| **Market Data** (Quotes, Price History) | `https://api.schwabapi.com/marketdata/v1/...` | `https://api.schwabapi.com/v1/marketdata/...` ← WRONG |

**Discovery:** The OAuth endpoints live at `/v1/oauth/authorize` and `/v1/oauth/token` — NOT under `/trader/v1`. This is the #1 integration pitfall. The portal's "Trader API" page shows the trader server URL, but OAuth is separate.

**Correct full URLs:**
```
OAuth:       https://api.schwabapi.com/v1/oauth/authorize
OAuth:       https://api.schwabapi.com/v1/oauth/token
Trader:      https://api.schwabapi.com/trader/v1/accounts/accountNumbers
Trader:      https://api.schwabapi.com/trader/v1/accounts/{id}/orders
Market Data: https://api.schwabapi.com/marketdata/v1/{symbol}/quotes
Market Data: https://api.schwabapi.com/marketdata/v1/pricehistory?symbol={symbol}&...
```

## 2. Price History URL Structure (Query Param, Not Path)

- **Quotes:** `GET /marketdata/v1/{symbol}/quotes` — symbol in **path**
- **Price History:** `GET /marketdata/v1/pricehistory?symbol={symbol}&...` — symbol as **query param**

Discovery: Looking at the portal's endpoint list, `/quotes` has `{symbol_id}` as a path parameter, but `/pricehistory` has no path parameters — symbol must be in the query string.

## 3. Redirect URI Issues

- `http://localhost:8080` may be rejected by Schwab portal as "invalid URL"
- `https://127.0.0.1:8080` passes validation but browser can't connect (bot runs HTTP server, not HTTPS)
- **Solution:** Use manual code entry — user copies the full code from browser address bar and pastes into terminal
- The code may include `&session=...` suffix that must be stripped before token exchange

## 4. Empty 404 Responses (No Response Body)

Symptoms: All endpoints return 404 with no JSON body, no error message.

**Causes (in order of likelihood):**
1. **Wrong base URL** — Using `/v1` instead of `/trader/v1` for accounts, OR using `/trader/v1/oauth` instead of `/v1/oauth`
2. **Token issued before full approval** — Delete `tokens.json` and re-authenticate
3. **Market data provisioning delay** — Can take 24-72 hours after app shows "Ready for Use"
4. **Account-level restriction** — Call Schwab support: 1-800-435-4000

**Diagnostic test:**
```python
curl -s -H "Bearer TOKEN" "https://api.schwabapi.com/trader/v1/accounts/accountNumbers"
curl -s -H "Bearer TOKEN" "https://api.schwabapi.com/marketdata/v1/AAPL/quotes"
```
If both return 404, check base URL. If only market data 404s, provisioning is pending.

## 5. Authorization Code Format

- Codes are URL-safe base64 strings, typically 70-80 characters
- May contain URL-encoded characters like `%40` (for `@`)
- May include `&session=...` suffix that must be stripped before token exchange
- Single-use and expire within minutes
- Handle these input formats: raw code, full URL, code+session

## 6. yfinance 1m Data Limitations

- `yfinance.download(period='Nd', interval='1m')` fails for N > ~8 days with "Only 8 days worth of 1m granularity data are allowed"
- **Workaround:** Use `Ticker.history(period='7d', interval='1m')` for single-symbol data
- For multi-symbol backtests, fetch in 7-day chunks and concatenate
- Multi-index columns may need flattening: `data.columns = data.columns.get_level_values(0)`

## 7. PDT Rule Status (June 2026)

FINRA's Pattern Day Trader ($25k minimum) rule was **repealed June 4, 2026**, replaced with intraday margin standards. Brokers have until October 20, 2027 to fully phase in. Small accounts are no longer PDT-restricted.

## 8. Live Trading Loop Must Track Positions

The backtest engine tracks `open_positions` and monitors SL/TP every tick. The main loop MUST also:
- Block duplicate entries per ticker
- Monitor positions for SL/TP exits every iteration
- Enforce max positions dynamically
- Close all positions at market close
- Calculate daily loss limit as percentage of actual account value (not hardcoded)

**Without position tracking, the bot will place unmanaged orders with no exit strategy.**
