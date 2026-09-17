# Cross-Platform GUI: Flask + pywebview

## Why This Stack

For a Schwab trading bot dashboard that must run on any PC (Windows, macOS, Linux) without installing heavy GUI frameworks:

- **tkinter** — broken on many systems (missing TK libs even after `pacman -Sy tk`)
- **PyQt5/customtkinter** — not installed, no Rust toolchain for Tauri
- **Flask + pywebview** — lightweight, cross-platform (WebKitGTK on Linux, WebKit on macOS, Edge on Windows), installs cleanly into venv

## Architecture

```
┌─────────────────────────────────────────┐
│  Native Window (pywebview)              │
│  ┌───────────────────────────────────┐  │
│  │  dashboard.html (JS shell)        │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  fetch('/api/scene')        │  │  │
│  │  │  innerHTML = fragment       │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
        │ HTTP (localhost:5000-5100)
        ▼
┌─────────────────────────────────────────┐
│  Flask App (gui/app.py)                 │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ GET /        │  │ GET /api/scene   │  │
│  │ dashboard    │  │ scene_html()     │  │
│  │ .html (JS)   │  │ returns fragment │  │
│  └─────────────┘  └──────────────────┘  │
└─────────────────────────────────────────┘
        │ reads
        ▼
┌─────────────────────────────────────────┐
│  tokens.json (OAuth tokens + hashValue) │
│  positions.json (open positions + PnL) │
└─────────────────────────────────────────┘
```

**Key insight:** The JS shell (`dashboard.html`) is NOT a Jinja template — it's a standalone HTML file that polls `/api/scene` and injects the fragment into `#root`. This avoids template confusion.

## File Layout

```
gui/
├── app.py              ← Flask + pywebview launcher
├── dashboard.html      ← JS shell (polls /api/scene every 3s)
├── styles.css          ← Dark btop-inspired CSS (may be unused if inline)
├── package.json        ← pyinstaller build stub
├── __init__.py         ← Empty, makes gui importable as package
└── __pycache__/        ← Cleaned before commits
```

## Top-of-File Import Fix

`app.py` must inject venv site-packages BEFORE any other imports so system Python can find flask/webview:

```python
import sys, os
VENV_SITE_PACKAGES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'venv', 'lib', 'python3.14', 'site-packages'
)
if os.path.isdir(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)

# NOW import flask, webview, etc.
from flask import Flask, Response, jsonify
import webview
```

## CWD Independence

All file paths must be relative to `app.py`, not CWD:

```python
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
TOKENS_FILE = os.path.join(BASE, 'tokens.json')
POSITIONS_FILE = os.path.join(BASE, 'positions.json')
DASHBOARD_FILE = os.path.join(HERE, 'dashboard.html')
```

This allows launching from any directory: `cd /anywhere && python /path/to/gui/app.py`.

## Dynamic Port Selection

```python
def _resolve_port():
    for port in range(5000, 5200):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            s.bind(('127.0.0.1', port))
            s.close()
            return port
        except OSError:
            continue
    return 5000
```

## HTML Fragment Template

The fragment returned by `/api/scene` matches the btop-style mockup. **No duplicate top/bottom bars, no chart column, no 7c column:**

```html
<div class="container">
  <div class="box bot-control-panel">...<!-- Start/Stop buttons, status --></div>
  <div class="box bot-panel">
    <div class="bot-title-row">
      <span class="bot-title">GLASS TB</span>
      <span class="bot-metrics bot-pnl-{{DAYNPNLCLS}}">
        <span class="metric"><span class="label">Cash:</span> <span class="value">{{CASH}}</span></span>
        <span class="metric"><span class="label">BP:</span> <span class="value">{{BP}}</span></span>
        <span class="metric"><span class="label">Value:</span> <span class="value">{{VALUE}}</span></span>
        <span class="metric"><span class="label">Day PnL:</span> <span class="value">{{DAYPNL}}</span></span>
      </span>
    </div>
    <div class="bot-second-row">
      <span class="pnl-label">Total PnL:</span>
      <span class="pnl-{{TOTALPNLCLS}}">{{TOTALPNL}}</span>
      <span class="ts">{{TIMESTAMP}}</span>
    </div>
  </div>
  <div class="box">
    <div class="market-header">BID/ASK</div>
    <table class="price-table">
      <thead><tr><th>Symbol</th><th>Price</th></tr></thead>
      <tbody>{{PRICE_ROWS}}</tbody>
    </table>
  </div>
  <div class="box">
    <div class="pos-header">POSITIONS</div>
    <div class="pos-box"><span class="pos-dot"></span>No open positions</div>
  </div>
  <div class="box trade-log">...</div>
</div>
```

**Note:** There is NO `top-box`, NO bottom `status-bar`, NO `7c` column, NO `Chart` column.

## Account Value Parsing (Critical)

Schwab returns `400 Bad Request` if you pass `?fields=portfolio` or any `?fields=<key>`. **Do not use `fields` param.** Fetch the full response and parse manually:

```python
r = requests.get(f'https://api.schwabapi.com/trader/v1/accounts/{hash}', headers=headers, timeout=10)
body = r.json()
acct = body.get('securitiesAccount') or body

# Positions
for sec in acct.get('positions', []):
    qty = sec.get('longQuantity', 0) - sec.get('shortQuantity', 0)
    ...

# Balances — try currentBalances first, then initialBalances
balances = acct.get('currentBalances') or acct.get('initialBalances') or {}
cash = (balances.get('cashAvailableForTrading')
        or balances.get('availableFunds')
        or balances.get('availableFundsNonMarginableTrade')
        or balances.get('settlementFunds')
        or balances.get('cashBalance')
        or balances.get('liquidationValue')
        or 0.0)

# Value fallback
if total_value == 0 and total_cash > 0:
    total_value = total_cash
```

## Color Palette (Mockup Match)

```css
/* borders */
border: 1px solid #5a7a9a;

/* live data, headers */
color: #7ec8e3;

/* background */
background: #0a0a12;
background: #0c0c16;

/* negative PnL */
color: #e06c75;

/* bar track background */
background: #14142a;
border: 1px solid #3a5a7a;
```

## Graceful Shutdown

```python
_shutdown = False

def _quit():
    global _shutdown, WINDOW
    _shutdown = True
    if WINDOW is not None:
        try:
            import webview
            webview.destroy(WINDOW)
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, lambda sig, frame: _quit())
signal.signal(signal.SIGTERM, lambda sig, frame: _quit())
atexit.register(_quit)
```

## Launch Script

Create `launch.sh` in the project root:

```bash
#!/usr/bin/env bash
cd "$(dirname "$0")"
exec venv/bin/python gui/app.py
```

`chmod +x launch.sh` — then `./launch.sh` launches the GUI.

## Common Pitfalls

### 1. Import Order
If `import flask` happens before `sys.path.insert(0, venv_site_packages)`, system Python fails with `ModuleNotFoundError`. The path fix MUST be at the very top of `app.py`.

### 2. price_html Signature
`price_html(ticker, price)` takes ticker as first arg. Do NOT reverse-lookup ticker from price — fails when no data loaded.

### 3. webview.start() Blocks
`webview.start()` blocks the main thread. In piped/background mode, it can cause TTY ioctl errors. For testing, verify routes + scene_html() via Flask test client, not by launching the window.

### 4. Jinja Confusion
`dashboard.html` is NOT a Jinja template — it's a standalone JS app. The fragment returned by `/api/scene` is built via string concatenation in Python, not template rendering. Don't add `{{...}}` to dashboard.html.

### 5. atexit sys.exit(0)
`_quit()` is registered with `atexit`. When the process exits (even normally), it calls `sys.exit(0)` which prints `SystemExit: 0` to stderr. Harmless but noisy. Exit code 124 from `timeout` means the GUI ran for the full timeout period (not a crash).

### 6. Venv Import Path
The venv path is constructed as `venv/lib/python3.14/site-packages`. If Python version changes (e.g., 3.15), update the path. The `sys.path.insert(0, ...)` handles this at runtime.

### 7. Bot Thread State Reset
`stop_bot()` must set `state['bot_running']=False` and `status='idle'` IMMEDIATELY. Users reject delays. Also use `_bot_run_wrapper()` to reset state when `bot.run()` exits naturally:

```python
def _bot_run_wrapper():
    global BOT_INSTANCE
    if BOT_INSTANCE is None:
        return
    try:
        BOT_INSTANCE.run()
    finally:
        state['bot_running'] = False
        state['bot_status'] = 'idle' if state['bot_status'] != 'error' else 'error'
        if BOT_INSTANCE is not None:
            BOT_INSTANCE._running = False
```

### 8. Tick Resilience
`tick()` must always reschedule the next call even if `fetch_data_sync()` throws:

```python
def tick():
    global _shutdown
    if _shutdown:
        return
    s = state
    if s.get('up_since') is None:
        s['up_since'] = time.perf_counter()
    s['uptime'] = time.perf_counter() - s['up_since']
    s['timer'] = time.time()
    s['timestamp'] = fmt_time()
    try:
        fetch_data_sync()
        s['refresh_count'] += 1
    except Exception as e:
        s['bot_error'] = f'Data refresh error: {str(e)[:100]}'
    if not _shutdown:
        t = threading.Timer(3.0, tick)
        t.daemon = True
        t.start()
```

## Status (2026-09-18 — latest)

- GlassTB: integrated bot + GUI pushed to https://github.com/re-glass/GlassTB
- Bot runs in background thread, dashboard shows Start/Stop + trade log
- UI: no duplicate sections, no 7c column, no chart column (Symbol + Price only)
- Account values: parsed from full `securitiesAccount` response (no `fields` param)
- Stop bot: button flips immediately to START BOT
- Tick: resilient (always reschedules)
- launch.sh: `./launch.sh` one-command launcher
- Cross-platform: WebKitGTK (Linux), WebKit (macOS), Edge (Windows)
