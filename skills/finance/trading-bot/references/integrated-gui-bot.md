# Integrated Bot + GUI (GlassTB)

GlassTB combines TradingBot and GUI into a single native application. TradingBot runs as a daemon thread inside the Flask/pywebview app; the dashboard polls `/api/scene` every 3s for live data + bot state.

## Architecture

```
launch.sh
  └── exec venv/bin/python gui/app.py

gui/app.py (Flask + pywebview)
  ├── Flask server
  │   ├── /              → serves dashboard.html (JS shell)
  │   ├── /api/scene     → returns live HTML fragment
  │   ├── /api/bot/start → POST: start TradingBot in background thread
  │   ├── /api/bot/stop  → POST: signal TradingBot to stop
  │   └── /api/bot/status → GET: JSON {running, status, strategy, paper, error}
  ├── pywebview native window (title: "GlassTB")
  ├── Data refresh loop (threading.Timer every 3s → fetch_data_sync)
  └── Bot thread (daemon: target=TradingBot.run)
```

## TradingBot GUI_MODE

When running inside the GUI, `TradingBot` needs `Config.GUI_MODE = True`:

```python
# trading_bot.py — Config class
GUI_MODE = False  # True = auto-continue on daily loss, skip signal handlers, skip blocking input

# In TradingBot.__init__:
def _setup_signal_handlers(self):
    if self.config.GUI_MODE:
        return  # Only main thread can set signal handlers
    signal.signal(signal.SIGINT, self._signal_handler)
    signal.signal(signal.SIGTERM, self._signal_handler)
    signal.signal(signal.SIGHUP, self._signal_handler)

# In run() daily-loss check:
if self._check_daily_loss():
    if self.config.GUI_MODE:
        log.info("GUI mode: auto-continuing (limit doubled)")
        self.config.MAX_DAILY_LOSS *= 2
    else:
        response = input("Continue trading? (y/n): ").strip().lower()
        ...
```

State tracking additions:
```python
# __init__
self._stop_requested = False
self._running = False

# run()
self._running = True
while not self._stop_requested:
    ...
self._running = False

# stop() — called from GUI
def stop(self):
    self._stop_requested = True

# status_dict property — exposes state to GUI
@property
def status_dict(self):
    return {
        'running': self._running,
        'strategy': self.strategy,
        'paper_trading': self.config.PAPER_TRADING,
        'tickers': self.config.TICKERS,
        'positions': dict(self.paper_positions),
        'daily_pnl': self.daily_pnl,
        'total_pnl': self.total_pnl,
        'account_value': self.account_value,
    }
```

## Bot Control API Routes

```python
BOT_THREAD = None
BOT_INSTANCE = None

@APP.route('/api/bot/start', methods=['POST'])
def bot_start():
    global BOT_THREAD, BOT_INSTANCE
    if state['bot_running']:
        return jsonify({'ok': False, 'error': 'Bot already running'})
    try:
        from trading_bot import TradingBot, Config
        Config.GUI_MODE = True
        Config.PAPER_TRADING = state.get('bot_paper', True)
        Config.STRATEGY = state.get('bot_strategy', 'mean_reversion')
        bot = TradingBot()
        BOT_INSTANCE = bot
        state['bot_running'] = True
        state['bot_status'] = 'running'
        t = threading.Thread(target=bot.run, daemon=True)
        t.start()
        BOT_THREAD = t
        return jsonify({'ok': True})
    except Exception as e:
        state['bot_status'] = 'error'
        state['bot_error'] = str(e)
        return jsonify({'ok': False, 'error': str(e)})

@APP.route('/api/bot/stop', methods=['POST'])
def bot_stop():
    global BOT_INSTANCE
    if not state['bot_running']:
        return jsonify({'ok': False, 'error': 'Bot not running'})
    try:
        if BOT_INSTANCE is not None:
            BOT_INSTANCE.stop()
        state['bot_status'] = 'stopping'
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@APP.route('/api/bot/status')
def bot_status():
    return jsonify({
        'running': state['bot_running'],
        'status': state['bot_status'],
        'strategy': state['bot_strategy'],
        'paper': state['bot_paper'],
        'error': state['bot_error'],
    })
```

## Bot Control Panel (HTML fragment)

```html
<div class="box bot-control-panel">
  <div class="bot-control-top">
    <span class="bot-status-label bot-running">RUNNING</span>
    <!-- or .bot-stopped / .bot-stopping -->
    <span class="bot-mode-label">PAPER</span>
    <button class="btn btn-start" onclick="toggleBot()">START BOT</button>
    <!-- or .btn-stop with STOP BOT text -->
  </div>
  <div class="bot-control-info">
    <span class="metric"><span class="label">Strategy:</span> <span class="value">mean_reversion</span></span>
    <span class="metric"><span class="label">Mode:</span> <span class="value">PAPER</span></span>
  </div>
  <!-- Error display (only when error present): -->
  <div class="bot-error">error message</div>
</div>
```

JavaScript toggle:
```javascript
window.toggleBot = function () {
  var btn = document.querySelector('.btn-start, .btn-stop');
  if (!btn || btn.disabled) return;
  var isStart = btn.classList.contains('btn-start');
  fetch('/api/bot/' + (isStart ? 'start' : 'stop'), { method: 'POST' })
    .then(r => r.json())
    .then(d => { if (!d.ok && d.error) alert('Bot: ' + d.error); })
    .catch(e => alert('Request failed: ' + e));
};
```

## Trade Log Persistence

```python
# State
state['trade_log'] = []

# Load on startup
def load_trade_log():
    if not os.path.isfile(TRADE_LOG_FILE):
        return []
    try:
        with open(TRADE_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_trade_log(log):
    try:
        with open(TRADE_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log[-500:], f)  # keep last 500
    except Exception:
        pass

def append_trade(entry):
    log = state.get('trade_log', [])
    log.append(entry)
    state['trade_log'] = log[-200:]  # keep last 200 in memory
    save_trade_log(log)
```

Trade log entry format:
```python
{
    'time': '14:38:15',
    'symbol': '/YM',
    'side': 'long',
    'qty': 1,
    'price': 52228.00,
    'pnl': 12.50,
    'reason': 'stop_loss'  # or 'take_profit', 'signal'
}
```

Trade log HTML panel:
```html
<div class="box">
  <div class="market-header">TRADE LOG</div>
  <div class="trade-log">
    <div class="trade-line">
      <span class="trade-time">14:38:15</span>
      <span class="trade-symbol">/YM</span>
      <span class="trade-side trade-side-long">LONG</span>
      <span class="trade-qty">1</span>
      <span class="trade-price">$52,228.00</span>
      <span class="trade-reason">stop_loss</span>
      <span class="trade-pnl-pos">+$12.50</span>
    </div>
  </div>
</div>
```

Empty state:
```html
<div class="trade-log-empty">No trades yet</div>
```

## launch.sh Pattern

```bash
#!/usr/bin/env bash
# Launch GlassTB (Trading Bot GUI)
cd "$(dirname "$0")"
exec venv/bin/python gui/app.py
```

Make executable: `chmod + launch.sh`

Key: use `exec` so the shell process is replaced by Python (signal handling stays clean). `cd "$(dirname "$0")"` makes it work regardless of where you run it from.

## State Dict

```python
state = {
    'app':          None,
    'templates':    {'style': ''},
    'shell':        '',
    'timer':        None,
    'up_since':     None,
    'uptime':       0.0,
    'cash':         0.0,
    'bp':           0.0,
    'value':        0.0,
    'daily_pnl':    0.0,
    'total_pnl':    0.0,
    'timestamp':    '',
    'prices':       {},
    'history':      {},
    'max_price':    0.0,
    'refresh_count': 0,
    'positions':    [],
    'trade_log':    [],
    'bot_running':  False,
    'bot_status':   'idle',     # idle | starting | running | stopping | error
    'bot_strategy': 'mean_reversion',
    'bot_paper':    True,
    'bot_error':    '',
}
```

## Window Title

```python
WINDOW = webview.create_window(
    'GlassTB',
    url,
    width=900,
    height=700,
    ...
)
```

Startup prints:
```python
print('GlassTB starting - window: GlassTB')
print(f'Refresh interval: 3s')
print('Press Ctrl+C to quit.')
```

## Common Pitfalls

1. **String concatenation with tuples** — `return ('a' 'b' 'c')` is NOT valid Python. Use `return 'a' + 'b' + 'c'` or `return ''.join([...])`. This is the #1 syntax error when building HTML fragments inline.

2. **Signal handlers in threads** — `signal.signal()` only works in the main thread. Skip when `GUI_MODE = True` (bot runs in background thread).

3. **Blocking input() in threads** — `input()` blocks the thread and freezes the GUI. Auto-continue instead.

4. **Daemon thread** — Bot thread must be `daemon=True` so it doesn't prevent the app from exiting.

5. **BOT_INSTANCE global** — Keep a module-level reference so `stop()` can signal the bot. Without it, `BOT_THREAD` is just a handle; the actual bot object is unreachable.

6. **`atexit` with `sys.exit(0)`** — The `_quit()` function called by `atexit` raises `SystemExit: 0` which prints "Exception ignored in atexit callback". This is harmless noise. Don't try to fix it.

7. **`tick()` must always reschedule** — If data refresh throws and `tick()` doesn't schedule the next call, prices go stale silently. Always wrap in try/except and schedule next tick regardless.

8. **Schwab `fields` param → 400 errors** — Account endpoint rejects `fields=portfolio`, `fields=positions`, etc. Fetch full `securitiesAccount` response and parse positions/balances directly.

9. **Account values all $0.00** — Caused by `fields` param rejection. Fix: no `fields` param, parse `securitiesAccount.currentBalances` or `.initialBalances`, fall back to `liquidationValue` then `cash` for display value.

## File Layout

```
GlassTB/
├── launch.sh              # One-command launcher
├── trading_bot.py         # TradingBot class (GUI_MODE support)
├── gui/
│   ├── __init__.py        # Empty (package marker)
│   ├── app.py             # Flask + pywebview + bot control
│   ├── dashboard.html     # Dark btop-style UI shell
│   ├── styles.css         # CSS (fallback)
│   └── package.json       # pyinstaller stub
├── tokens.json            # OAuth tokens
├── positions.json         # Position persistence
├── trade_log.json         # Trade history
├── requirements.txt
├── README.md
├── FAANG_SCALPING_STRATEGY.md
└── REVIEW.md
```

## Verification

Same pattern as GUI dashboard: use Flask test client, don't launch the window.

```python
import gui.app as g
html = g.scene_html()
# assert 'GLASS TB' in html
# assert 'bot-control-panel' in html
# assert 'TRADE LOG' in html

client = g.APP.test_client()
r = client.get('/api/scene')
r = client.post('/api/bot/start')
r = client.get('/api/bot/status')
```

## Session-Specific Notes

- User asked to "combine the 2 into one solid app" — this is the result
- User named the app "GlassTB"
- Copy of scalping_bot/ was made and called GlassTB before integration
- PyGObject had to be installed in venv for GTK+WebKit backend on Linux
- Force push was needed (remote had diverging history from the standalone GUI repo)
- PAT was provided for push authentication
