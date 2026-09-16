# Risk Management Formulas

## Per-Trade Risk (2% Rule)

```python
account_value = 1000.0      # Current account equity
risk_pct = 0.02              # 2% risk per trade
risk_amount = account_value * risk_pct  # $20
```

## Position Sizing (ATR-Based)

```python
atr = 0.50                   # 14-period ATR
sl_mult = 1.0                # Stop loss = 1.0x ATR
stop_distance = atr * sl_mult  # $0.50

qty = max(1, int(risk_amount / stop_distance))  # 40 shares
actual_risk = qty * stop_distance                # $20.00
```

## Daily Loss Limit (Kill Switch)

```python
max_daily_loss_pct = 0.05    # 5% max daily loss
daily_loss_limit = -(account_value * max_daily_loss_pct)  # -$50

# In main loop:
if daily_pnl < daily_loss_limit:
    print("Daily loss limit hit. Stopping.")
    break  # Stop trading for the day
```

## Reward-to-Risk Ratio

```python
sl_mult = 1.0
tp_mult = 1.5                # 1.5:1 reward-to-risk

sl = entry - (atr * sl_mult)
tp = entry + (atr * tp_mult)

# Risk: $0.50 per share
# Reward: $0.75 per share
# R:R = 1.5:1
```

## Maximum Positions

```python
max_positions = 2             # For small accounts (<$1000)

# Guard:
if len(open_positions) >= max_positions:
    continue  # Don't enter new positions
```

## Account-Sized Limits

| Account Size | Max Risk (2%) | Daily Limit (5%) | Max Positions |
|--------------|---------------|------------------|---------------|
| $500         | $10           | $25              | 1-2           |
| $1,000       | $20           | $50              | 2             |
| $5,000       | $100          | $250             | 3             |
| $25,000+     | $500          | $1,250           | 5             |

## Kill Switch Implementation

```python
# Hardcoded (WRONG):
if daily_pnl < -100:

# Dynamic (RIGHT):
daily_loss_limit = -(account_value * max_daily_loss_pct)
if daily_pnl < daily_loss_limit:
    break
```

## Correlation Warning

FAANG stocks are highly correlated. With $1,000:
- 2 positions ≈ 1 effective bet
- Consider reducing to 1 position max
- Or diversify across sectors

## Discretionary Override

Always allow manual kill switch:

```python
try:
    while True:
        # Trading logic
        pass
except KeyboardInterrupt:
    print("Manual kill switch activated.")
    open_positions.clear()
```
