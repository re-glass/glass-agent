# TUI Token Refresh Handling

## Problem
The TUI (`tui.py`) reads the access token from `tokens.json` once at startup via `load_token()`. When the trading bot refreshes the token (writes a new `access_token` to `tokens.json`), the TUI continues using the stale token and API calls start failing with 401/403 errors. The TUI appears to "stop loading data" even though it's still running.

## Fix
Re-read `tokens.json` at the start of each refresh cycle instead of caching the token at startup.

In `main()`:
```python
while True:
    try:
        # Re-read token each cycle so token refreshes are picked up
        token = load_token()
        if token is None:
            console.print('[yellow]Warning: token missing — will retry[/]')
            time.sleep(5)
            continue
        # ... rest of cycle
```

The `load_token()` function itself stays the same (reads file each call), but the key change is calling it inside the loop rather than once before the loop.

## Why this happens
The trading bot and TUI run as separate processes. The bot refreshes its OAuth token periodically and writes the new token to `tokens.json`. The TUI, if it cached the token at startup, never sees the update.

## Files
- `tui.py` — main TUI dashboard
- `tokens.json` — shared token file (read/written by both bot and TUI)
