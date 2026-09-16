# Safety Features

## Graceful Shutdown

On kill (Ctrl+C or `kill` command), the bot:
1. Receives shutdown signal (SIGINT/SIGTERM)
2. Closes all open positions at market price
3. Places closing orders (if live trading)
4. Saves final state to `positions.json`
5. Exits cleanly

## Position Persistence

Every position change is saved to `positions.json`:
```json
{
  "positions": {
    "/YM": {
      "side": "long",
      "qty": 50,
      "entry": 52500.0,
      "sl": 52495.0,
      "tp": 52510.0,
      "entry_time": "2026-09-15T13:47:00"
    }
  },
  "daily_pnl": 16.79,
  "total_pnl": 16.79,
  "account_value": 304.92,
  "date": "2026-09-15",
  "timestamp": "2026-09-15T14:00:00"
}
```

## Crash Recovery

On startup, bot checks `positions.json`:
- If date matches today → restore positions
- If date is old → clear file, start fresh

## Signal Handler Pattern

```python
import signal

def _setup_signal_handlers(self):
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    signal.signal(signal.SIGHUP, self._signal_handler)

def _signal_handler(self, signum, frame):
    self._close_all_positions()
    sys.exit(0)
```

## Pitfalls

1. **datetime not JSON serializable** — Always convert `datetime` objects to strings before JSON serialization:
   ```python
   if 'entry_time' in pos_copy and isinstance(pos_copy['entry_time'], datetime):
       pos_copy['entry_time'] = pos_copy['entry_time'].isoformat()
   ```

2. **Loading strings back to datetime** — On load, convert strings back:
   ```python
   pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
   ```

3. **Duplicate bot instances** — Check for existing process before starting:
   ```bash
   ps aux | grep trading_bot | grep -v grep
   ```
