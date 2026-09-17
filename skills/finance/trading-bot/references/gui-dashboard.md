# Cross-Platform GUI Dashboard (Flask + pywebview)

## Architecture

```
app.py (Flask server + pywebview launcher)
  ├── /           → serves dashboard.html (JS shell with #root + fetch loop)
  └── /api/scene  → returns scene_html() fragment (panels only)

dashboard.html    → standalone JS app: inline <style>, #root div, fetch('/api/scene') loop
styles.css        → dark btop-inspired CSS (may be unused if dashboard.html has inline styles)
package.json      → pyinstaller build stub (for future .exe packaging)
```

## Stack

- **Flask** serves two routes on localhost
- **pywebview** opens a native OS window: WebKitGTK (Linux), WebKit (macOS), Edge (Windows)
- **Vanilla JS** in `dashboard.html` polls `/api/scene` every 3s and injects into `#root`

## Import Fix (CRITICAL)

`app.py` MUST inject the venv site-packages path at the VERY TOP of the file, BEFORE any other imports:

```python
VENV_SITE_PACKAGES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'venv', 'lib', 'python3.14', 'site-packages'
)
if os.path.isdir(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)

import flask          # ← these come AFTER the sys.path insert
from flask import Flask, Response
import webview        ← this installs as "webview", not "pywebview"
```

Without this, `/usr/bin/python3` cannot find `flask` or `webview` (package installs as `webview`, pip name is `pywebview`).

## CWD-Independent Paths

All paths must be relative to `app.py` via `os.path.dirname(os.path.abspath(__file__))`, not CWD:

```python
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
TOKENS_FILE = os.path.join(BASE, 'tokens.json')
POSITIONS_FILE = os.path.join(BASE, 'positions.json')
DASHBOARD_FILE = os.path.join(HERE, 'dashboard.html')
STYLES_FILE = os.path.join(HERE, 'styles.css')
```

## Fragment Template (`scene_html()`)

The fragment is pure Python string concatenation — **NO Jinja `{{}}` placeholders**. Dashboard.html is NOT a template; it's a standalone JS app.

```python
def scene_html():
    st = state
    return (
        '<div class="container">'
        '<div class="box top-box">No open positions</div>'
        # ... all panels as string concatenation ...
        '</div>'
    )
```

### price_html(ticker, price, max_price)

Signature MUST take `ticker` as first arg. Uses ticker to determine candle vs bar:

- `/GC`, `/ES` → OHLC candlestick with `.wick` + `.cbody`
- `/YM`, `/NQ`, `/CL`, `/SI` → horizontal bar with `.bar-fill`

### positions_html(positions)

Returns either "No open positions" box (when empty) or row-per-position markup.

## Layout (Mockup-Matched)

```
┌─────────────────────────────────────────────────┐  top-box: "No open positions"
├─────────────────────────────────────────────────┤  status-bar: cursor + "refresh in 3s • uptime 24s • ctrl+c quit"
│ [RUNNING] PAPER                    [STOP BOT]   │  bot-control-panel: status + mode + button
│ GLASS TB     Cash: $304.92  BP: $304.92  ...    │  bot-title + metrics on SAME LINE
│ Total PnL: +113.27          2026-09-17 14:38:15│  bot-second-row
├─────────────────────────────────────────────────┤
│                   BID/ASK                        │  market-header centered
│ Symbol │ Price      │ Chart      │ 7c           │  price-table
│ /YM    │ $52,228.00 │ ████████   │ -            │  bar for /YM
│ /GC    │ $4,389.90  │ ┃▓┃        │ -            │  candle for /GC
│ /ES    │ $7,703.75  │ ┃▓┃        │ -            │  candle for /ES
│ /NQ    │ $29,711.00 │ ████████   │ -            │  bar for /NQ
│ /CL    │ $101.94    │ █          │ -            │  bar for /CL
│ /SI    │ $65.86     │ █          │ -            │  bar for /SI
├─────────────────────────────────────────────────┤
│                   POSITIONS                      │  pos-header with ::after underline
│              ■ No open positions                 │  pos-box with pos-dot + text
├─────────────────────────────────────────────────┤
│                   TRADE LOG                      │  trade-log panel (last 50 entries)
│ 14:38:15  /YM   LONG  1  $52,228.00  stop_loss  │  trade-line row
├─────────────────────────────────────────────────┤  bottom status-bar: cursor + text
└─────────────────────────────────────────────────┘
```

## Color Palette

| Element | Color |
|---------|-------|
| Background | `#0a0a12` |
| Panel bg | `#0c0c16` |
| Borders | `#5a7a9a` (light blue) |
| Header/text | `#7ec8e3` (light cyan) |
| Secondary text | `#8aa0b8` |
| Negative PnL | `#e06c75` (red) |
| White cursor | `#ffffff` |

## OHLC Candlestick Math (fixed — previous version was wrong)

```python
hist_vals = state['history'].get(ticker, [])[-5:]
if len(hist_vals) >= 2:
    o, h, l, c = hist_vals[0], max(hist_vals), min(hist_vals), hist_vals[-1]
else:
    o = h = l = c = px

rng = max(h - l, px * 0.001, 0.01)
scale = 26.0 / rng

body_h = max(3, abs(c - o) * scale)
body_top = (min(o, c) - l) * scale
wick_top = (h - l) * scale

wick_css = f'top:{max(0, wick_top)}px;'
body_css = f'top:{max(0, body_top)}px;height:{max(3, body_h)}px;'

# Candle CSS:
# .candle{display:inline-block;position:relative;width:16px;height:30px}
# .wick{position:absolute;left:50%;transform:translateX(-50%);width:1px;background:#7ec8e3;top:0;bottom:0}
# .cbody{position:absolute;left:1px;right:1px;background:#7ec8e3;min-height:2px}
```

## Horizontal Bar Math (fixed — previous linear scale was wrong)

Use **log scale** so small-priced assets (/CL at $100) show visible bars alongside large ones (/YM at $52k):

```python
import math
if px > 0:
    log_px = math.log10(max(px, 1))
    log_max = math.log10(max(max_price, 10))
    log_min = log_max - 2.0  # 2 orders of magnitude range
    pct = max(0.05, min(0.98, (log_px - log_min) / (log_max - log_min)))
    bar_w = max(4, int(74 * pct))
else:
    bar_w = 4

# Bar CSS:
# .bar-track{display:inline-block;height:11px;background:#14142a;border:1px solid #3a5a7a;border-radius:1px;width:80px;position:relative;overflow:hidden}
# .bar-fill{display:block;height:100%;background:#7ec8e3;transition:width 0.5s}
```

## Data Refresh Loop (tick) — Must Always Reschedule

```python
def tick():
    """Called every 3s; refresh data, schedule next. Always reschedules."""
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
    # schedule next (always, even on error)
    if not _shutdown:
        t = threading.Timer(3.0, tick)
        t.daemon = True
        t.start()
```

**Pitfall:** If `tick()` doesn't reschedule after an error, prices stop updating. The user sees stale data and doesn't know why. Always schedule the next tick regardless of success/failure.

## Common Pitfalls

1. **Import order bug** — `import flask` at top of `app.py` happens before `sys.path` is patched. Fix: `sys.path.insert(0, venv_site_packages)` at the VERY TOP.

2. **Jinja confusion** — `dashboard.html` is NOT a Jinja template. Fragment is pure Python string concat. Don't mix paradigms.

3. **price_html(ticker, ...)` signature** — Must take `ticker` as first arg for candle/bar assignment.

4. **CWD-dependent paths** — Use `os.path.dirname(os.path.abspath(__file__))` for all file paths.

5. **`webview.start()` blocks** — Main thread blocks. For testing, use Flask test client (`APP.test_client()`), don't launch the window.

6. **`gui/__init__.py` required** — Empty file so `import gui.app` works as package import.

7. **Duplicate bot instances** — Kill existing `tui.py`/`gui/app.py` before launching to avoid port conflicts.

8. **Flask debug/reloader** — Must disable: `APP.debug = False`, `use_reloader=False`. Double-reloader spawns duplicate Flask processes.

9. **Port conflicts** — Dynamic port selection (5000–5100 range) avoids collisions. `_resolve_port()` scans for free port.

10. **`fetch_data_sync()` runs in main thread** — Not in a background thread. The `tick()` function uses `threading.Timer` but this only works after `webview.start()` has begun. In practice, the first `tick()` call is manual, then subsequent ones schedule via `threading.Timer`.

## Running

```bash
cd /home/reg/scalping_bot
/usr/bin/python3 gui/app.py          # works via sys.path injection
# OR
./venv/bin/python gui/app.py         # venv python (no PYTHONPATH needed)
```

## Verification

For ad-hoc verification, write a test script that:
1. Imports `gui.app` (with `sys.path.insert(0, venv_site_packages)` and `sys.path.insert(0, project_root)`)
2. Calls `g.scene_html()` and asserts layout tokens are present
3. Uses `g.APP.test_client()` to verify `/` returns shell and `/api/scene` returns fragment
4. Does NOT launch the window (webview.start() blocks)

DO NOT include a `time.sleep()` + `SIGTERM` launch test in automated verification — `webview.start()` blocks forever. Test routes + HTML output only.

## Session-Specific Notes

- User pivoted from TUI (Rich-based) to cross-platform GUI after TUI duplication issues persisted through multiple rewrite attempts
- Mockup reference: `/home/reg/.hermes/images/clip_20260917_143905_2.png` (btop-style dark dashboard)
- User's exact requirement: "make an application that can run on any PC regardless of OS"
- Chose pywebview over tkinter (tkinter broken: missing TK libs), PyQt5 (not installed), Tauri (no Rust toolchain)
- Venv: Python 3.14, `webview` (pywebview 6.2.1) + `flask` installed via `uv pip` or `venv/bin/pip`
- **GlassTB** is the app name — unified bot + GUI. Copy of `scalping_bot/` was made and called `GlassTB/` before integration
- `PyGObject` had to be installed in venv for GTK+WebKit backend on Linux
- Force push was needed to `TradingBot-code` remote (had diverging standalone GUI history)
- PAT provided for GitHub push authentication
- **Critical syntax trap:** String concatenation inside `return (...)` parenthesized expression creates a tuple of strings, not a single HTML string — and causes `SyntaxError` on the closing paren. Use `return ''.join(parts)` or explicit `+` concatenation in a variable first. The `parts = []; parts.append(...); return ''.join(parts)` pattern is the safe default.
- **Mockup-driven layout:** Build what the mockup shows, not what you would have chosen. User shared a btop-style reference and expected exact match: panel order, light-blue borders (`#5a7a9a`), light-cyan text (`#7ec8e3`), SCALPING BOT title on same line as metrics, green candle bars in Chart col, dash in 7c col, cursor block in status bars.
- **User corrections (2026-09-17):** 
  - "im not seeing the repo in github" — repo wasn't created on GitHub, just pushed to existing remote. Always create new repo via API if user says "make a repo called X".
  - "the price isnt updating and the account values are all 0.00" — two bugs: (1) `fields=portfolio` causing 400s; (2) `tick()` not rescheduling after error.
  - "can you remove the duplicate sections also the 7c column" — user doesn't want top-box + bottom status bar duplicates. Keep only essential panels.
  - "charts dont look like that" — candle/bar rendering must match mockup. User rejected charts that looked like dots or invisible bars. Must use log scale for bars, absolute positioning for candles.
  - "when i hit stop bot the button didnt change back to START BOT" — `stop_bot()` must update state immediately, not wait for thread to exit.
- **Schwab `fields` param 400 error:** The `fetch_data_sync()` function initially used `fields=portfolio` and `fields=<key>` params which caused 400 errors. Fixed by removing `fields` and parsing full `securitiesAccount` response.
- **Candlestick CSS:** `.candle` needs explicit `width:16px`, `.wick` needs `top:0;bottom:0` (full height), `.cbody` needs `position:absolute;left:1px;right:1px` for proper rendering.
- **Bar log scale:** Linear scale (`px / max_price`) made small-priced assets (/CL at ~$100) show near-zero width bars next to /YM at ~$52k. Fixed with `math.log10` scale.
- **`tick()` reschedule:** Initial version didn't wrap in try/except or always reschedule — if `fetch_data_sync` threw, prices stopped updating silently.
