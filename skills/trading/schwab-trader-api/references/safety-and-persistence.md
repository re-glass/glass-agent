# Safety Features and Position Persistence

## Graceful Shutdown

The bot handles SIGINT, SIGTERM, and SIGHUP signals to ensure positions are closed on kill:

```python
import signal

def _setup_signal_handlers(self):
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    signal.signal(signal.SIGHUP, self._signal_handler)

def _signal_handler(self, signum, frame):
    sig_name = signal.Signals(signum).name
    log.warn(f"Received {sig_name} — initiating graceful shutdown...")
    self._close_all_positions()
    sys.exit(0)
```

## Position Persistence

Positions are saved to `positions.json` on every change (open, close, daily reset).

### Save Format
```json
{
  "positions": {
    "/GC": {
      "side": "short",
      "qty": 10,
      "entry": 4397.0,
      "sl": 4400.0,
      "tp": 4392.0,
      "entry_time": "2026-09-15T11:54:03.123456"
    }
  },
  "daily_pnl": 7.82,
  "total_pnl": 7.82,
  "account_value": 304.92,
  "date": "2026-09-15",
  "timestamp": "2026-09-15T11:54:03.123456"
}
```

### Datetime Serialization
datetime objects must be converted to strings for JSON:
```python
# Saving
if isinstance(pos_copy['entry_time'], datetime):
    pos_copy['entry_time'] = pos_copy['entry_time'].isoformat()

# Loading
if isinstance(pos['entry_time'], str):
    pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
```

### Crash Recovery
On startup, if `positions.json` exists and is from the same day, positions are restored. Old day files are cleared.

## Live Trading Safety

When `paper_trading: False`, the `_close_all_positions()` method:
1. Gets latest price from API
2. Calculates P&L
3. Places closing order (SELL for longs, BUY for shorts)
4. Logs all actions
5. Clears positions and saves state

## Risk Management

- Daily loss limit: 5% of account (hard stop)
- Max positions: 2 concurrent
- Risk per trade: 2% of account
- Max position size: 10% of account

## Pitfall: positions.json with datetime

**Error:** `Object of type datetime is not JSON serializable`
**Fix:** Convert datetime to string before serialization, parse back on load.
