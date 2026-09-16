# Trading Loop Architecture: Critical Patterns

## The Max Positions Bug (CRITICAL)

**Symptom:** Bot opens multiple positions on startup, exceeding max_positions.

**Cause:** The max positions check was placed INSIDE the for loop that iterates tickers:

```python
# WRONG — allows N positions in one iteration
for ticker in TICKERS:
    if len(open_positions) >= MAX_POSITIONS:
        continue
    signal = generate_signal(...)
    if signal:
        open_positions.append(...)
```

**Fix:** Check BEFORE the loop:

```python
# CORRECT — only enters one position per loop iteration
if len(open_positions) >= MAX_POSITIONS:
    time.sleep(LOOP_INTERVAL)
    continue

for ticker in TICKERS:
    signal = generate_signal(...)
    if signal:
        open_positions.append(...)
        break  # Optional: stop after first entry
```

**Pitfall:** Even with the check before the loop, multiple signals can fire in one iteration if you don't break after entry. For strict single-entry-per-loop, add a `break` after opening a position.

## First-Loop Instant Entry Bug

**Symptom:** Bot enters positions immediately on startup.

**Cause:** On the first loop pass, indicators may produce signals because:
- Price history is fresh from API
- RSI/VWAP values hit thresholds due to warmup effects
- No prior context exists

**Fix:** Skip signal processing on the first loop:

```python
def run(self):
    self._first_loop = True
    while True:
        if self._first_loop:
            self._first_loop = False
            log.info("First loop — skipping signal processing")
            self._print_status()
            time.sleep(LOOP_INTERVAL)
            continue
        # ... normal processing
```

## Silent Bot / Appears Frozen

**Symptom:** No output for long periods, user thinks bot is dead.

**Cause:** When max positions is reached or outside market hours, the bot sleeps silently.

**Fix:** Always print status, even when idle:

```python
if self._check_max_positions():
    log.status(f"Max positions ({len(pos)}/{MAX})")
    self._print_status()  # ALWAYS print prices
    time.sleep(LOOP_INTERVAL)
    continue
```

## Datetime JSON Serialization

**Symptom:** `Object of type datetime is not JSON serializable` when saving positions.

**Cause:** `datetime` objects from `datetime.now()` are not JSON-serializable.

**Fix:** Convert before saving, restore after loading:

```python
# Saving
positions_copy = {}
for ticker, pos in self.paper_positions.items():
    pos_copy = pos.copy()
    if 'entry_time' in pos_copy and isinstance(pos_copy['entry_time'], datetime):
        pos_copy['entry_time'] = pos_copy['entry_time'].isoformat()
    positions_copy[ticker] = pos_copy

# Loading
for ticker, pos in positions.items():
    if 'entry_time' in pos and isinstance(pos['entry_time'], str):
        pos['entry_time'] = datetime.fromisoformat(pos['entry_time'])
```

## Graceful Shutdown Pattern

```python
import signal
import sys

def _setup_signal_handlers(self):
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    signal.signal(signal.SIGHUP, self._signal_handler)

def _signal_handler(self, signum, frame):
    sig_name = signal.Signals(signum).name
    log.warn(f"Received {sig_name} — closing positions...")
    self._close_all_positions()
    sys.exit(0)
```

**Pitfall:** SIGKILL (`kill -9`) cannot be caught — positions will remain open. Always prefer SIGTERM.

## Position Persistence

Save state on every change:
- After opening a position
- After closing a position
- On graceful shutdown
- Daily reset

File: `positions.json`

```json
{
  "positions": {
    "/YM": {"side": "long", "qty": 10, "entry": 52500.0, "sl": 52450.0, "tp": 52600.0, "entry_time": "2026-09-15T10:30:00"}
  },
  "daily_pnl": 25.50,
  "total_pnl": 150.75,
  "account_value": 1050.0,
  "date": "2026-09-15",
  "timestamp": "2026-09-15T10:35:00"
}
```

## Loop Interval vs API Rate Limits

Schwab rate limit: ~120 requests/minute.

With 6 tickers and 30-second loops:
- 12 price history requests per loop (1 per ticker)
- 6 latest price requests for status line
- 18 requests per 30 seconds = ~36/minute

Well within limits. Reduce interval or ticker count if you hit 429 errors.
