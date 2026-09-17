# Live Dashboard / TUI for Trading Bot

## When to Build

User wants a real-time visual dashboard showing:
- Account overview (cash, buying power, P&L)
- Live prices with mini sparkline charts
- Open positions with current P&L
- Status bar with last update time

## Tech Choices

### Rich (preferred for simple dashboards)

**Pros:** Lightweight, no async complexity, works in any terminal, easy to install (`pip install rich`).

**Cons:** No built-in auto-refresh timer; must manage loop manually.

**Pattern:**
```python
from rich.live import Live
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED

console = Console()
with Live(console=console, refresh_per_second=0.33, vertical_overflow='visible') as live:
    while True:
        content = build_content()   # returns Group(*widgets)
        live.update(content)
        time.sleep(3)
```

**Pitfall:** `Live` with `refresh_per_second` controls the refresh rate. Don't mix with `time.sleep` inside the loop — `Live` handles scheduling.

**Pitfall:** Lists of renderables cannot be passed to `live.update()`. Wrap in `Group(*items)`.

### Textual (for complex interactive apps)

**Pros:** Full widget system, async support, event handling, layout system.

**Cons:** Heavier dependency, steeper learning curve, async patterns can complicate simple dashboards.

**When to choose:** User wants interactive elements (buttons, keybindings beyond quit, modal screens, multiple screens).

**When to avoid:** Simple read-only monitoring dashboard — Rich `Live` is simpler and less error-prone.

## Data Fetching

### Schwab API (market data)

```python
import requests

M = 'https://api.schwabapi.com/marketdata/v1'

def get_prices(token, tickers):
    prices = {}
    for t in tickers:
        r = requests.get(
            M + '/pricehistory',
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
            params={'symbol': t, 'periodType': 'day', 'period': 1,
                    'frequencyType': 'minute', 'frequency': 1},
            timeout=5,
        )
        if r.status_code == 200:
            c = r.json().get('candles', [])
            prices[t] = c[-1]['close'] if c else None
        else:
            prices[t] = None
    return prices
```

**Pitfall:** Futures have no working `/quotes` endpoint. Always use `pricehistory` for all price data.

**Pitfall:** Each API call takes ~1-2 seconds. With 6 tickers, a full refresh cycle is ~6-12 seconds. Set refresh interval accordingly (3-5 seconds between full refreshes is reasonable).

### Account info

```python
TR = 'https://api.schwabapi.com/trader/v1'

def get_account(token):
    r = requests.get(TR + '/accounts/accountNumbers',
                     headers={'Authorization': 'Bearer ' + token}, timeout=5)
    if r.status_code == 200:
        h = r.json()[0]['hashValue']
        r2 = requests.get(TR + '/accounts/' + h,
                          headers={'Authorization': 'Bearer ' + token},
                          params={'fields': 'positions'}, timeout=5)
        if r2.status_code == 200:
            return r2.json()['securitiesAccount']['currentBalances']
    return {'cash': 0, 'buyingPower': 0, 'liquidationValue': 0}
```

**Pitfall:** Account endpoint requires `hashValue` from `/accounts/accountNumbers`, not the plain account number.

## Sparkline Charts

ASCII sparklines give a quick visual of price movement without needing a full chart library.

```python
def spark(candles):
    if not candles:
        return 'N/A'
    closes = [c.get('close', 0) for c in candles]
    if len(closes) < 2:
        return '┄'
    lo = min(closes)
    hi = max(closes)
    rng = hi - lo if hi != lo else 1
    chars = '▁▂▃▄▅▆▇█'
    return ''.join(
        chars[int((c - lo) / rng * (len(chars) - 1))]
        for c in closes
    )[-20:]
```

**Pitfall — Index out of range:** The formula `chars[int((c - lo) / rng * len(chars))]` can produce index `len(chars)` when `c == hi`. Always multiply by `len(chars) - 1` to keep index in `[0, len(chars)-1]`.

**Pitfall — Empty data:** Handle empty candle list (return 'N/A') and single-candle list (return '┄') before computing min/max.

## Persistence

### What to persist

After each refresh cycle, write to JSON files:

| File | Contents |
|------|----------|
| `positions.json` | Open positions, daily_pnl, total_pnl |
| `current_prices_cache.json` | Last fetched prices + candles |
| `historical_cache.json` | Full candle history per ticker |
| `trade_log.json` | All executed trades (entry, exit, P&L) |

### Pattern

```python
def save_positions(data):
    with open('positions.json', 'w') as f:
        json.dump(data, f, indent=2)

def save_prices_cache(prices, candles):
    with open('current_prices_cache.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'prices': prices,
            'candles': candles,
        }, f, indent=2)
```

**Pitfall:** Don't commit cache files to git. Add to `.gitignore`:
```
current_prices_cache.json
historical_cache.json
```

## Display Layout

### Account Overview Panel

Show: Cash, Buying Power, Account Value, Daily P&L, Total P&L.
Color P&L green (positive) or red (negative).

### Prices Table

Columns: Symbol, Price, Chart (sparkline).
One row per ticker. Show 'N/A' if price unavailable.

### Positions Table

Columns: Symbol, Side (LONG/SHORT), Qty, Entry, Current, P&L.
Show '—' row if no positions open.

### Status Bar

Bottom line: Last update timestamp + "Press Ctrl+C to quit".

## Common Pitfalls

1. **Sparkline index error** — Always use `len(chars) - 1` in the index calculation.
2. **Rich Live with list** — `live.update([a, b, c])` fails. Use `Group(a, b, c)`.
3. **API rate limits** — 6 tickers × 2 API calls each = 12 calls per cycle. At 3-second cycles, that's 240 calls/minute. Schwab limit is ~120/min. Add small delays between calls or reduce ticker count.
4. **Stale token** — If API returns 401, token expired. Refresh or re-authenticate. See `references/tui-token-refresh.md`.
5. **No positions file** — Handle missing `positions.json` gracefully (start with empty positions).
6. **Terminal size** — Long sparklines or wide tables may wrap on small terminals. Keep tables compact.
7. **Stutter / flicker** — Calling `console.clear()` at the top of every refresh cycle and then reprinting all panels causes visible stutter/flicker every interval. Fix: do NOT clear; do a single-pass render of a bounded block that overwrites the previous output, then sleep for the remainder of the interval (`max(0.1, REFRESH_INTERVAL - spent)`). This keeps the display stable and removes the stutter. The tradeoff is that the output block must be sized to fit the terminal so it doesn't scroll.
8. **Mockup-driven layout** — When the user shares a visual mockup of the desired TUI, match it exactly: panel order, which panels repeat, title alignment (left vs right), border color, text color (light gray vs bright), column structure (e.g. Symbol | Price | Chart | 7c), and sparkline style (horizontal bars scaled to max price vs candle mini-bars vs classic sparkline chars). Do not impose your own layout guesses — build what the mockup shows.
