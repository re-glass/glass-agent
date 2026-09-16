---
name: automated-trading
description: >
  Build, test, and deploy automated trading systems with broker APIs.
  Covers strategy development, backtesting, paper trading, risk management,
  and live execution. Use when building trading bots, integrating with
  broker APIs (Schwab, Alpaca, Interactive Brokers, etc.), or working with
  market data feeds. Triggers: trading bot, algorithmic trading, backtest,
  paper trading, market data API, broker API, order execution, position
  management, risk management, day trading, scalping, mean reversion.
---

# Automated Trading Systems

Build production-ready trading bots with proper risk management, position tracking, and broker API integration.

## When This Skill MUST Be Used

**ALWAYS invoke this skill for:**
- Building or modifying trading bots/strategies
- Integrating with broker APIs (Schwab, Alpaca, IBKR, etc.)
- Backtesting trading strategies
- Setting up paper trading workflows
- Implementing risk management (position sizing, stop losses, daily limits)
- Debugging market data or order execution issues

## Core Principles

### 1. Paper Trade First, Always
Never go live without 2-4 weeks of successful paper trading. Backtests lie — live market conditions (slippage, fills, latency) differ.

### 2. Position Tracking is Mandatory
A trading bot must track:
- Open positions per ticker
- Entry price, quantity, side
- Stop loss and take profit levels
- Daily P&L
- Maximum position limits

**Without position tracking, the bot will:**
- Enter duplicate positions
- Lose track of risk
- Fail to exit at SL/TP

### 3. Risk Management Rules
- **Per-trade risk:** 1-2% of account per trade
- **Daily loss limit:** 5% max drawdown per day (kill switch)
- **Max positions:** Limit concurrent positions (2 for small accounts)
- **Position sizing:** `qty = max(1, int(risk_amount / stop_distance))`

### 4. Broker API Quirks
- Market data access often requires separate approval (24-48 hour delay)
- Tokens can be issued before full access is granted — re-authenticate if 404s persist
- OAuth codes may include session parameters that need stripping
- Rate limits apply (typically 120 requests/minute)

## Workflow

### Phase 1: Strategy Development
1. Define entry/exact rules (must be computer-executable, not subjective)
2. Define exit rules (SL/TP/trailing stop/time-based)
3. Implement indicators (VWAP, RSI, Bollinger Bands, ATR, etc.)
4. Backtest on historical data (minimum 100 trades, multiple months)

### Phase 2: Backtesting
1. Use walk-forward optimization (test multiple parameter sets)
2. Verify profit factor > 1.1
3. Check trade distribution (not concentrated in few lucky trades)
4. Analyze per-ticker performance (drop losing tickers)
5. Validate max drawdown is acceptable

### Phase 3: Paper Trading
1. Implement paper trading mode (no real orders)
2. Track simulated positions with SL/TP monitoring
3. Run for 2-4 weeks minimum
4. Verify signals generate correctly
5. Confirm no duplicate entries or missed exits

### Phase 4: Live Trading (Only After Paper Success)
1. Switch `paper_trading: False`
2. Start with minimum position size
3. Monitor first few trades closely
4. Keep daily loss limit active
5. Have manual kill switch ready

## Common Pitfalls

### No Position Tracking
```python
# WRONG: Just placing orders
if signal:
    api.place_order(ticker, side, qty)

# RIGHT: Track positions
if signal and ticker not in open_positions and len(open_positions) < max_positions:
    api.place_order(ticker, side, qty)
    open_positions[ticker] = {'entry': price, 'sl': sl, 'tp': tp, 'qty': qty}
```

### Hardcoded Risk Values
```python
# WRONG: Hardcoded $100 limit
if daily_pnl < -100:

# RIGHT: Dynamic percentage
daily_loss_limit = -(account_value * max_daily_loss_pct)
if daily_pnl < daily_loss_limit:
```

### Missing Exit Monitoring
```python
# WRONG: Place order and forget
api.place_order(ticker, 'BUY', qty)

# RIGHT: Monitor for SL/TP every tick
for ticker, pos in open_positions.items():
    if pos['side'] == 'long':
        if current_price <= pos['sl']:
            close_position(ticker, 'SL')
        elif current_price >= pos['tp']:
            close_position(ticker, 'TP')
```

## Reference Files

- [`references/schwab-api.md`](references/schwab-api.md) — Schwab API specifics, OAuth flow, scopes, 404 debugging
- [`references/position-tracking.md`](references/position-tracking.md) — Position tracking patterns and state management
- [`references/risk-management.md`](references/risk-management.md) — Risk calculation formulas and kill switch patterns

## Safety Rules

1. **Never commit credentials** — Use `.gitignore` for tokens.json, .env, API keys
2. **Always have a kill switch** — Daily loss limit that stops all trading
3. **Log everything** — Every signal, order, exit, and error must be logged
4. **Test auth separately** — Verify API access before running main loop
5. **Start small** — Minimum position size when going live

## Example: Mean Reversion Scalping Bot

```python
# Entry: Price extended from VWAP + RSI extreme + BB touch
if deviation < -0.3 and rsi < 30 and bb_pctb < 0.1:
    signal = 1  # Long

# Exit: ATR-based SL/TP
stop_distance = atr * 1.0
sl = entry - stop_distance
tp = entry + (stop_distance * 1.5)  # 1.5:1 reward-to-risk

# Position sizing: 2% risk per trade
risk_amount = account_value * 0.02
qty = max(1, int(risk_amount / stop_distance))
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 404 on all endpoints | Market data not approved | Wait 24-48h or re-authenticate |
| 404 on quotes only | Missing MarketData scope | Re-auth with correct scopes |
| Duplicate entries | No position tracking | Add `open_positions` dict check |
| No exits | Missing SL/TP monitoring | Add exit check loop |
| Token expired | Refresh token expired | Delete tokens.json, re-auth |
| Rate limit hit | Too many API calls | Cache account info, don't call every tick |
