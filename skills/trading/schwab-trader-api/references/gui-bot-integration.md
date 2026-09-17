# GUI-Bot Integration Pattern

## How to Run TradingBot in a Background Thread

The TradingBot `run()` method blocks. In a GUI context, it must run in a background thread so the Flask server and pywebview window remain responsive.

```python
import threading

BOT_THREAD = None
BOT_INSTANCE = None

def start_bot():
    """Start TradingBot in a background thread."""
    global BOT_THREAD, BOT_INSTANCE
    if state['bot_running']:
        return {'ok': False, 'error': 'Bot already running'}
    try:
        from trading_bot import TradingBot, Config
        Config.GUI_MODE = True          # Disable input() prompts
        Config.PAPER_TRADING = True     # Always paper-trade from GUI
        bot = TradingBot()
        BOT_INSTANCE = bot
        state['bot_running'] = True
        state['bot_status'] = 'running'
        t = threading.Thread(target=bot.run, daemon=True)
        t.start()
        BOT_THREAD = t
        return {'ok': True}
    except Exception as e:
        state['bot_status'] = 'error'
        state['bot_error'] = str(e)
        return {'ok': False, 'error': str(e)}

def stop_bot():
    """Signal TradingBot to stop."""
    global BOT_INSTANCE
    if not state['bot_running']:
        return {'ok': False, 'error': 'Bot not running'}
    if BOT_INSTANCE is not None:
        BOT_INSTANCE.stop()
    state['bot_status'] = 'stopping'
    return {'ok': True}
```

## Bot Class Changes for GUI_MODE

Add these to `trading_bot.py`:

```python
class Config:
    GUI_MODE = False  # When True, auto-continue on daily loss (no input blocks)

class TradingBot:
    def __init__(self):
        # ... existing state ...
        self._stop_requested = False
        self._running = False

    def _setup_signal_handlers(self):
        # GUI mode runs in a thread — skip signal handlers (main thread only)
        if self.config.GUI_MODE:
            return
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def stop(self):
        """Signal the bot loop to exit on next iteration."""
        self._stop_requested = True

    @property
    def status_dict(self):
        """Return bot state for GUI display."""
        return {
            'running': self._running,
            'strategy': self.strategy,
            'paper_trading': self.config.PAPER_TRADING,
            'positions': dict(self.paper_positions),
            'daily_pnl': self.daily_pnl,
            'total_pnl': self.total_pnl,
            'account_value': self.account_value,
        }

    def run(self):
        self._running = True
        # ... setup ...
        while not self._stop_requested:
            # ... main loop ...
        self._running = False
```

## Daily Loss Handling in GUI Mode

When `Config.GUI_MODE = True`, the daily loss prompt is replaced with auto-continuation:

```python
if self._check_daily_loss():
    log.warn(f"Daily loss limit hit (${self.daily_pnl:.2f})")
    if self.config.GUI_MODE:
        log.info("GUI mode: auto-continuing (limit doubled)")
        self.config.MAX_DAILY_LOSS *= 2
    else:
        response = input("Continue trading? (y/n): ").strip().lower()
        # ...
```

## Flask Routes for Bot Control

```python
@APP.route('/api/bot/start', methods=['POST'])
def bot_start():
    return jsonify(start_bot())

@APP.route('/api/bot/stop', methods=['POST'])
def bot_stop():
    return jsonify(stop_bot())

@APP.route('/api/bot/status')
def bot_status():
    return jsonify({
        'running': state['bot_running'],
        'status': state['bot_status'],
        'strategy': state['bot_strategy'],
        'paper': state['bot_paper'],
    })
```

## Bot Control Panel (HTML)

The dashboard renders a bot control panel between the status bar and the account metrics:

```html
<div class="box bot-control-panel">
  <div class="bot-control-top">
    <span class="bot-status-label bot-running">RUNNING</span>
    <span class="bot-mode-label">PAPER</span>
    <button class="btn btn-stop" onclick="toggleBot()">STOP BOT</button>
  </div>
  <div class="bot-control-info">
    <span class="metric"><span class="label">Strategy:</span> <span class="value">mean_reversion</span></span>
    <span class="metric"><span class="label">Mode:</span> <span class="value">PAPER</span></span>
  </div>
</div>
```

## Trade Log

Track trades in `trade_log.json` and render in the dashboard:

```python
def append_trade(entry):
    """Persist a trade entry."""
    log = state.get('trade_log', [])
    log.append(entry)
    state['trade_log'] = log[-200]
    save_trade_log(log)

def trade_log_html():
    """Render the trade log panel."""
    log = state.get('trade_log', [])
    # ... render last 50 entries ...
```

Each trade entry contains: `time, symbol, side, qty, price, pnl, reason`.

## JS Toggle

```javascript
window.toggleBot = function () {
  var btn = document.querySelector('.btn-start, .btn-stop');
  if (!btn || btn.disabled) return;
  var isStart = btn.classList.contains('btn-start');
  fetch('/api/bot/' + (isStart ? 'start' : 'stop'), { method: 'POST' })
    .then(r => r.json())
    .then(d => { if (!d.ok && d.error) alert('Bot: ' + d.error); });
};
```

## Status States

| State | Color | Button | Behavior |
|-------|-------|--------|----------|
| idle/stopped | Gray "STOPPED" | Green "START BOT" | Click to start |
| running | Cyan "RUNNING" | Red "STOP BOT" | Click to stop |
| stopping | Orange "STOPPING" | Disabled | Waiting for loop to exit |
| error | Red error text | Green "START BOT" | Shows error message |

## Stop Bot Button State (Critical)

The stop button MUST flip back to "START BOT" immediately when clicked — users rejected a delay. Two changes needed:

### 1. stop_bot() updates state immediately
```python
def stop_bot():
    global BOT_INSTANCE
    if not state['bot_running']:
        return {'ok': False, 'error': 'Bot not running'}
    try:
        if BOT_INSTANCE is not None:
            BOT_INSTANCE.stop()
        # Immediately update state — do NOT wait for thread to exit
        state['bot_running'] = False
        state['bot_status'] = 'idle'
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
```

### 2. Wrapper resets state when bot.run() exits naturally
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

Use `target=_bot_run_wrapper` instead of `target=bot.run` when starting the thread.

### 3. Remove 'stopping' status
Don't use a 'stopping' status — it creates a dead state. Only use: `idle`, `running`, `error`.

## Account Data Fetching (Schwab API Pitfall)

**Critical:** Schwab returns `400 Bad Request` when passing `fields` query params. Do NOT use `?fields=portfolio` or `?fields=<key>`.

### Correct Pattern
```python
# Get full account data — NO fields param
r = requests.get(
    f'https://api.schwabapi.com/trader/v1/accounts/{hash}',
    headers=headers,
    timeout=10
)
body = r.json()
acct = body.get('securitiesAccount') or body

# Parse positions
for sec in acct.get('positions', []):
    qty = sec.get('longQuantity', 0) - sec.get('shortQuantity', 0)
    cur = sec.get('marketValue', 0)
    avg = sec.get('averagePrice', 0)
    # ...

# Parse balances — check multiple keys
balances = acct.get('currentBalances') or acct.get('initialBalances') or {}
cash = (balances.get('cashAvailableForTrading')
        or balances.get('availableFunds')
        or balances.get('availableFundsNonMarginableTrade')
        or balances.get('settlementFunds')
        or balances.get('cashBalance')
        or balances.get('liquidationValue')
        or 0.0)

# Fallback: value = cash when no positions
if total_value == 0 and total_cash > 0:
    total_value = total_cash
```

## Tick Resilience

`tick()` must always reschedule the next call, even on error:

```python
def tick():
    global _shutdown
    if _shutdown:
        return
    # ... update uptime ...
    try:
        fetch_data_sync()
        state['refresh_count'] += 1
    except Exception as e:
        state['bot_error'] = f'Data refresh error: {str(e)[:100]}'
    # Always reschedule
    if not _shutdown:
        t = threading.Timer(3.0, tick)
        t.daemon = True
        t.start()
```

## Key Pitfalls

1. **Thread safety:** Bot writes to `state['trade_log']` and `state['bot_status']`. Flask reads these. Python's GIL makes simple dict operations atomic — no lock needed for basic types.
2. **Signal handlers:** Only the main thread can set signal handlers. Skip them when `GUI_MODE=True`.
3. **Blocking prompts:** `input()` blocks the thread. Always use `GUI_MODE=True` to auto-continue.
4. **Daemon threads:** `daemon=True` ensures the thread dies when the main process exits.
5. **`webview.start()` blocks:** The GUI main thread is consumed by pywebview. Bot runs in a separate thread. Flask runs in yet another daemon thread.
6. **No duplicate UI sections:** User explicitly removed the top `No open positions` box (redundant with positions panel) and bottom status-bar (duplicate of top). Keep the dashboard minimal — one status bar at top only.
7. **No 7c column:** Removed per user request. The BID/ASK table has 3 columns: Symbol, Price, Chart.
8. **Chart rendering matters:** User rejected the initial chart output ("charts dont look like that"). Candles must be 16px wide with absolute-positioned wick+body. Bars must use log10 scale so small-priced assets are visible alongside large ones.
9. **Schwab API rejects `fields` param:** Returns 400 with cryptic error. Fetch full response and parse manually.
10. **Stop button must flip immediately:** Update state in `stop_bot()`, don't wait for thread exit.
