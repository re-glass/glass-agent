# FAANG Scalping Bot — Session Reference

## What Was Built

A Schwab API-based mean reversion scalping bot for FAANG stocks (AAPL, GOOGL, META, AMZN, NFLX) on 1-minute bars.

## Final Parameters

| Parameter | Value |
|-----------|-------|
| Strategy | Mean reversion only (trend following removed) |
| Entry | Price >0.3% from VWAP + RSI <30 or >65 + BB %B <0.1 or >0.9 |
| Stop Loss | 1.0x ATR |
| Take Profit | 1.5x ATR |
| Risk per Trade | 2% of account |
| Max Daily Loss | 5% (kill switch) |
| Max Positions | 2 concurrent |

## Files

```
/home/reg/scalping_bot/
├── live_bot.py                 ← Main bot (verified)
├── enhanced_backtest.py        ← Optimization backtest
├── FAANG_SCALPING_STRATEGY.md  ← Strategy reference
├── REVIEW.md                   ← Code review findings
├── README.md                   ← GitHub README
├── requirements.txt            ← Dependencies
└── .gitignore                  ← Excludes tokens.json, venv/
```

## Backtest Results

| Setting | Result |
|---------|--------|
| 48 days, 1015 trades | +$1,695 P&L |
| Win Rate | 43.5% |
| Profit Factor | 1.15 |
| Max Drawdown | -$593 |
| Best Ticker | META (+$1,057) |
| Worst Ticker | AAPL (-$202) |

## Schwab API Endpoints Used

```
POST /v1/oauth/token           ← Auth
GET  /v1/accounts/accountNumbers
GET  /v1/accounts/{accountId}
GET  /v1/marketdata/{symbol}/pricehistory
GET  /v1/marketdata/{symbol}/quotes
POST /v1/accounts/{accountId}/orders
```

## Key Lessons Learned

### 1. yfinance 1m Data
`yf.download()` fails for 1-minute data beyond ~8 days. Use `Ticker.history()`:
```python
t = yf.Ticker(ticker)
data = t.history(period='7d', interval='1m')
```

### 2. OAuth Redirect URI Must Match
Schwab portal requires `https://` redirect. The bot must use the same URI in `SCHWAB_CONFIG`. If the redirect fails, manual code entry works.

### 3. Authorization Code Parsing
The full redirect URL contains `code=XXX&session=YYY`. Parse only the code:
```python
code = raw.split('&')[0].strip()  # If pasted as URL
# OR
code = parse_qs(query).get('code', [''])[0]  # If pasted as full URL
```

### 4. Position Tracking is Mandatory
A trading bot must track open positions to:
- Prevent duplicate entries per ticker
- Enforce max positions limit
- Monitor SL/TP exits
- Calculate daily P&L for kill switches

### 5. Daily Loss Limit Must Be Dynamic
```python
# WRONG: Hardcoded
if daily_pnl < -100:

# RIGHT: Percentage of actual account
daily_loss_limit = -(account_value * max_daily_loss_pct)
if daily_pnl < daily_loss_limit:
```

### 6. 404 Errors Before API Approval
Schwab returns 404 on ALL endpoints (quotes, price history, accountNumbers) until market data access is fully provisioned. This is normal — wait 24-48 hours after approval.

## GitHub Repository

https://github.com/re-glass/TradingBot-code.git

## Status (Last Updated: 2026-09-11)

- Bot code complete and verified (6/6 tests pass)
- Paper trading mode enabled
- Waiting for Schwab market data approval
- User plans to paper trade for 2-4 weeks before considering live trading
