# Position Tracking Patterns

## The Problem

A trading bot without position tracking will:
- Enter duplicate positions on the same ticker
- Lose track of how much capital is at risk
- Fail to monitor stop losses and take profits
- Exceed maximum position limits

## The Solution

Track positions in a dictionary keyed by ticker:

```python
open_positions = {
    'AAPL': {
        'side': 'long',       # 'long' or 'short'
        'qty': 40,
        'entry': 150.00,
        'sl': 149.50,
        'tp': 150.75,
        'entry_time': datetime.now()
    }
}
```

## Entry Guard

Before entering a new position, check:

```python
if ticker in open_positions:
    continue  # Already in position

if len(open_positions) >= max_positions:
    continue  # At max positions
```

## Exit Monitoring

Every tick, check all open positions:

```python
for ticker, pos in open_positions.items():
    current_price = get_current_price(ticker)
    
    if pos['side'] == 'long':
        if current_price <= pos['sl']:
            # Stop loss hit
            pnl = (pos['sl'] - pos['entry']) * pos['qty']
            close_position(ticker, pnl)
        elif current_price >= pos['tp']:
            # Take profit hit
            pnl = (pos['tp'] - pos['entry']) * pos['qty']
            close_position(ticker, pnl)
    
    else:  # short
        if current_price >= pos['sl']:
            pnl = (pos['entry'] - pos['sl']) * pos['qty']
            close_position(ticker, pnl)
        elif current_price <= pos['tp']:
            pnl = (pos['entry'] - pos['tp']) * pos['qty']
            close_position(ticker, pnl)
```

## Market Close

At 4:00 PM, close all positions:

```python
if now.hour == 16 and now.minute == 0:
    for ticker, pos in list(open_positions.items()):
        close_price = get_current_price(ticker)
        if pos['side'] == 'long':
            pnl = (close_price - pos['entry']) * pos['qty']
        else:
            pnl = (pos['entry'] - close_price) * pos['qty']
        close_position(ticker, pnl)
    open_positions.clear()
```

## Paper Trading vs Live

Use separate tracking dicts:

```python
paper_positions = {}  # Simulated positions
open_positions = {}   # Real positions from broker

# In paper mode:
if paper_trading:
    paper_positions[ticker] = position_data
    # Monitor paper_positions for exits
else:
    open_positions[ticker] = position_data
    # Monitor open_positions for exits
```

## Daily Reset

Clear positions at market open each day:

```python
if datetime.now().date() != today:
    today = datetime.now().date()
    daily_pnl = 0.0
    open_positions.clear()
    paper_positions.clear()
```
