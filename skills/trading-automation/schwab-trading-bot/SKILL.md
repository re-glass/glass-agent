---
name: schwab-trading-bot
description: Build automated trading bots using the Charles Schwab API (OAuth2, market data, order placement). Covers API endpoints, futures vs stock symbol formats, position persistence, graceful shutdown, and strategy optimization.
tags: [trading, schwab, api, futures, automation, python]
---

# Schwab Trading Bot

Build production-ready automated trading bots using the Charles Schwab API.

## When to use

- User wants to automate trading stocks or futures via Schwab
- User wants live market data, order execution, or position tracking
- User wants strategy backtesting/optimization
- User needs graceful shutdown and position persistence

## Architecture

```
project/
├── trading_bot.py         ← Main bot (Config + Logger + SchwabAPI + TradingBot classes)
├── optimize.py            ← Parameter grid search
├── strategy_comparison.py ← Backtest multiple strategies
├── positions.json         ← Active position tracking (auto-generated)
└── tokens.json            ← OAuth tokens (auto-generated, gitignored)
```

## API Endpoints

| Category | Base URL |
|----------|----------|
| OAuth | `https://api.schwabapi.com/v1/oauth/authorize` |
| Token Exchange | `https://api.schwabapi.com/v1/oauth/token` |
| Market Data | `https://api.schwabapi.com/marketdata/v1/pricehistory` |
| Account/Orders | `https://api.schwabapi.com/trader/v1/accounts/...` |

## Critical API Quirks

### Symbol Formats
- **Stocks:** `AAPL`, `GOOGL` (same everywhere)
- **Futures (Schwab):** `/YM`, `/GC`, `/ES`, `/NQ`, `/CL`, `/SI`
- **Futures (yfinance):** `YM=F`, `GC=F`, `ES=F`, `NQ=F`, `CL=F`, `SI=F`

### Account ID
- `/accounts/accountNumbers` returns both `accountNumber` and `hashValue`
- **All subsequent account calls require `hashValue`**, not `accountNumber`
- Using accountNumber returns `{"message":"Invalid account number"}`

### Price Data
- `pricehistory` endpoint uses `symbol` as **query param**: `?symbol=/YM`
- `/quotes` endpoint does **NOT work for futures** (returns 404)
- For live futures prices, use `pricehistory` with `period=1, frequency=1`
- Response has nested price fields:
  - `quote.lastPrice` — **LIVE price** (use this)
  - `extended.lastPrice` — **STALE price** (avoid)
  - `regular.regularMarketLastPrice` — same as quote.lastPrice

### Authentication
- OAuth2 with authorization code flow
- Token expiry: ~30 minutes
- Refresh token lasts ~7 days
- Tokens saved to `tokens.json`

## Safety Patterns

### Graceful Shutdown
```python
import signal

def _setup_signal_handlers(self):
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)

def _signal_handler(self, signum, frame):
    self._close_all_positions()
    sys.exit(0)
```

### Position Persistence
```python
def _save_positions(self):
    # Convert datetime to string for JSON
    positions_copy = {}
    for ticker, pos in self.paper_positions.items():
        pos_copy = pos.copy()
        if 'entry_time' in pos_copy:
            pos_copy['entry_time'] = pos_copy['entry_time'].isoformat()
        positions_copy[ticker] = pos_copy
    with open('positions.json', 'w') as f:
        json.dump({'positions': positions_copy, ...}, f)

def _load_positions(self):
    # Convert entry_time string back to datetime
    for pos in positions.values():
        pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
```

## Strategy Optimization

Grid search across:
- ATR SL multiplier: [0.8, 1.0, 1.2, 1.5]
- ATR TP multiplier: [1.2, 1.5, 1.8, 2.0]
- RSI oversold: [25, 30, 35]
- RSI overbought: [65, 70, 75]
- VWAP deviation: [0.2, 0.3, 0.4]
- BB std dev: [1.5, 2.0, 2.5]

**Best found (futures, 1-min, 14 days):**
- ATR SL=1.0, TP=2.0, RSI=25/75, VWAP=0.3, BB=1.5
- PF: 1.39, P&L: $2,199, Win%: 40.4%, MaxDD: $406

## Position Sizing

```python
risk_amount = account_value * 0.02
stop_distance = atr * atr_sl_mult
qty = max(1, int(risk_amount / stop_distance))
```

## Pitfalls

1. **Wrong API base URL** — OAuth is `/v1/oauth/`, market data is `/marketdata/v1/`, trader is `/trader/v1/`
2. **Using accountNumber instead of hashValue** — causes "Invalid account number"
3. **Using extended.lastPrice** — returns stale data; always use `quote.lastPrice`
4. **No datetime serialization** — `positions.json` fails with `Object of type datetime is not JSON serializable`
5. **Missing signal handlers** — positions lost on Ctrl+C or kill
6. **Not checking `candles` key** — pricehistory returns `{"symbol": "...", "candles": [...]}`
