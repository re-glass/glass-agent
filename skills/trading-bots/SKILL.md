---
name: trading-bots
description: Build and deploy automated trading bots — broker APIs, data fetching, order management, and regulatory compliance. Use when the user asks about building a trading bot, connecting to a broker, fetching market data, placing orders, or trading rules.
---

# Trading Bots

Class-level skill for building automated trading systems: broker integration, market data, order management, and regulatory compliance.

## Trigger Conditions

Reach for this skill when the user asks about:
- Building a trading bot or automated trading system
- Connecting to a broker API (Schwab, Alpaca, Interactive Brokers, etc.)
- Fetching real-time or historical market data
- Placing/canceling orders programmatically
- Trading rules (PDT, margin, settlement, pattern day trader)
- Backtesting strategies

## Regulatory Context

### Pattern Day Trader (PDT) Rule — REPEALED
As of June 4, 2026, FINRA repealed the PDT rule. The old rule required $25,000 minimum equity for margin accounts that execute 4+ day trades in 5 days. It has been replaced with **intraday margin standards**. Brokers have an 18-month phase-in window until October 20, 2027.

**Key change for bot builders:** Accounts under $25,000 are no longer blocked from day trading by the PDT rule. However, intraday margin requirements still apply — check with your broker for specifics.

**Old rule (pre-June 2026):** Margin account under $25k → 3 day trades per 5 business days, then restricted.

**New rule (post-June 2026):** No PDT designation, but brokers may impose their own intraday margin requirements.

### Settlement Rules
- T+1 settlement for equities (trade date + 1 business day)
- Cash accounts: cannot sell shares bought with unsettled funds (free-riding restriction)
- Margin accounts: no settlement-based trading restrictions, but PDT-style rules may apply

## Market Data Fetching

### yfinance 1-Minute Data Limitation
`yfinance.download()` fails for 1-minute data beyond ~8 days. Use `Ticker.history()` instead:

```python
# BAD: Fails for 1m data beyond 8 days
data = yf.download(ticker, period='25d', interval='1m')

# GOOD: Works for 1m data (still limited to ~30 days total)
t = yf.Ticker(ticker)
data = t.history(period='7d', interval='1m')
```

**Workaround for more data:** Fetch in 7-8 day chunks and concatenate. Note that yfinance limits total 1m data to ~30 days per request.

## Broker API Authentication

### OAuth2 Pattern (Schwab, many modern brokers)
Most modern broker APIs use OAuth2. Common pitfall: the redirect URI must match exactly between the app registration and your code.

**Schwab-specific:**
- Redirect URI must be `https://` (not `http://`) in the portal
- `https://localhost:8080` or `https://127.0.0.1:8080` are typical choices
- If the redirect fails (browser shows "connection refused"), the bot should fall back to **manual code entry**

### Manual OAuth Fallback
When the local HTTP server can't capture the callback (HTTPS redirect, port blocked, etc.):

1. Open browser to the OAuth URL
2. User logs in, gets redirected to a URL with `?code=LONGCODE&session=...`
3. Copy the full URL or just the code value
4. Bot parses out the `code=` parameter

**Critical parsing detail:** Authorization codes may contain URL-encoded characters (e.g., `%40` for `@`). If the user pastes the full URL with `&session=...`, split on `&` and take only the code portion:

```python
raw = input("Enter code: ").strip()
if 'code=' in raw:
    query = urlparse(raw).query if raw.startswith('http') else raw.split('?')[-1]
    code = parse_qs(query).get('code', [''])[0]
else:
    code = raw.split('&')[0].strip()
```

### Token Storage
Save tokens to a JSON file (excluded from git via .gitignore). Refresh tokens before expiry (typically 30 minutes for access tokens, 7 days for refresh tokens).

## Order Management

### Position Tracking
A real trading bot must track open positions to:
- Prevent duplicate entries on the same ticker
- Enforce max positions limit
- Monitor stop-loss and take-profit levels
- Calculate daily P&L for kill switches

**Paper trading vs. live:** Gate all real order placement behind a `paper_trading` config flag. In paper mode, track positions in-memory and simulate exits.

### Daily Loss Limit
Implement a hard kill switch based on percentage of account value, not a hardcoded dollar amount:

```python
daily_loss_limit = -(account_value * max_daily_loss_pct)
if daily_pnl < daily_loss_limit:
    # Stop trading for the day
```

### Stop-Loss / Take-Profit
For scalping strategies, ATR-based stops are common:
- Stop Loss: Entry ± (ATR × multiplier)
- Take Profit: Entry ± (ATR × multiplier × reward_risk_ratio)

Monitor positions every tick and exit when price hits SL/TP.

## Verification Patterns

Before going live with any trading bot:
1. **Paper trade first** — at least 2-4 weeks of simulated trading
2. **Verify all endpoints** — test each API call (quotes, orders, account info)
3. **Check rate limits** — don't poll account info every tick
4. **Log everything** — every signal, order, fill, and error
5. **Have a kill switch** — daily loss limit + manual interrupt (Ctrl+C)

## Pitfalls

1. **yfinance 1m data:** Don't use `yf.download()` for intraday. Use `Ticker.history()`.
2. **OAuth redirect URI:** Must match portal exactly. Use manual fallback if localhost is problematic.
3. **Token expiry:** Access tokens expire (~30 min). Implement refresh logic.
4. **Position tracking:** Never place orders without tracking open positions. Prevents duplicate entries and enforces risk limits.
5. **Market hours:** Check market hours (9:30 AM - 4:00 PM ET) before trading. Don't hold positions overnight unless intended.
6. **Settlement:** Cash accounts have T+1 settlement. Don't sell unsettled shares.
