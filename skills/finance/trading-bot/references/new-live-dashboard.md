# Live Dashboard / TUI for Trading Bot

## When to Build

User wants a real-time visual dashboard showing:
- Account overview (cash, buying power, P&L)
- Live prices with mini sparkline/candle charts
- Open positions with current P&L
- Status bar with last update time

## Tech Choices

### Rich (preferred for simple dashboards)

**Pros:** Lightweight, no async complexity, works in any terminal, easy to install (`pip install rich`).

**Cons:** No built-in auto-refresh timer; must manage loop manually.

### Textual (for complex interactive apps)

**Pros:** Full widget system, async support, event handling, layout system.

**Cons:** Heavier dependency, steeper learning curve. Avoid for simple read-only monitoring dashboards — Rich is simpler and less error-prone.

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

## Sparkline / Candle Charts

### Classic sparkline (price movement over time)

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

### Horizontal candle bar (price magnitude relative to max)

For a "chart" column that shows a green bullish bar scaled to price/max_price:

```python
def candle_bar(p, max_price):
    if max_price <= 0:
        return Text('-', style='bright_black')
    ratio = (p / max_price) if max_price > 0 else 0.0
    width = max(1, int(ratio * 22))
    return Text('\u2588' * width, style='green')
```

Pick the style the mockup calls for. The mockup in this project used green horizontal bars (not classic sparkline chars) in the Chart column, with `-` in the 7c column.

## Refresh Loop — The One Pattern That Works Everywhere

### Problem statement

Two symptoms look similar but have different causes:
1. **Stutter / flicker** — reprinting panels one at a time (multiple `console.print()` calls) combines with `console.clear()` to produce visible flicker every interval. The panels re-flow independently.
2. **Duplication (stacking)** — each refresh appends a full copy of the scene underneath the previous one, so the terminal fills up with stacked frames.

Both are fixed by the same pattern: **build ONE `Group` from all panels, `console.clear()` once, `console.print(scene)` once, then sleep for the remainder of the interval.**

### Single-pass render pattern (preferred — works in all terminals and pipes)

```python
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, SQUARE

console = Console()
REFRESH_INTERVAL = 3

while True:
    cycle_start = time.time()
    try:
        # ... fetch data ...

        # Build ONE Group from all panels (do not print panels individually)
        scene = Group(
            build_top_box(positions),
            '\n',
            build_status_bar(uptime),
            '\n',
            build_scalping_bot_panel(account, dpnl, tpnl, now),
            '\n',
            build_bid_ask_table(prices, candles_by_ticker),
            '\n',
            build_positions_panel(positions),
            '\n',
            build_status_bar(uptime),   # bottom status bar
        )

        console.clear()
        console.print(scene)

        # Persist
        save_positions(...)
        save_prices_cache(...)

        # Sleep remainder of interval (not full REFRESH_INTERVAL)
        spent = time.time() - cycle_start
        time.sleep(max(0.1, REFRESH_INTERVAL - spent))

    except KeyboardInterrupt:
        break
    except Exception as e:
        console.print(Text(f'Error: {e}', style='red'))
        time.sleep(REFRESH_INTERVAL)
```

**Why this works:**
- Single `clear()` + single `print(scene)` — no per-panel re-flow, no flicker
- Sleeping the remainder of the interval (not the full interval) keeps the cycle at a steady cadence regardless of how long the API calls took
- Works in TTY and in pipes / `script` captures / `subprocess.Popen(stdout=PIPE)` — no `Live` dependency, no `is_terminal` branch

**What NOT to do:**
- Multiple `console.print()` calls per cycle (causes flicker)
- `Live` with manual refresh (works on TTY but breaks in pipes — see below)
- `time.sleep(REFRESH_INTERVAL)` after already spending most of the interval in API calls (drifts the cadence)

### Do NOT use Rich Live for this dashboard pattern

Rich `Live` with `auto_refresh=False` + manual `live.refresh()` works for TTY-only use, but it does NOT update in non-TTY contexts (pipe, `script -q -c`, `subprocess.Popen(stdout=PIPE)`). In those contexts `Live.update()` emits a full copy each refresh instead of overwriting in place, so the output accumulates and looks like duplication. This makes `Live` a poor choice when the same binary may be run in a pipe for verification or capture.

**Diagnostic:** if you suspect duplication, run the TUI headless for N seconds, kill it, and count occurrences of a unique scene marker like `'SCALPING BOT'` or `'BID/ASK'`. With the single-pass clear+print pattern, the count equals the number of cycles (≈ N / REFRESH_INTERVAL) and stays bounded. With stacking it grows without bound. Note: status bars appear twice per scene (top + bottom), so status-bar count ≈ 2 × scene count — that is NOT duplication.

**If you must use Live:** branch on `console.is_terminal`. Use Live for real terminals, clear+single-print for everything else.

```python
if console.is_terminal:
    with Live(console=console, refresh_per_second=4, transient=False,
              vertical_overflow='visible', auto_refresh=False) as live:
        while True:
            scene = build_scene()
            live.update(scene)
            live.refresh()
            time.sleep(sleep_for)
else:
    while True:
        scene = build_scene()
        console.clear()
        console.print(scene)
        time.sleep(sleep_for)
```

Given the tradeoffs, prefer the unconditional clear+single-print pattern above. It is simpler, more predictable, and works identically whether the user runs it in a terminal or a pipe.

## Persistence

After each refresh cycle, write to JSON files:

| File | Contents |
|------|----------|
| `positions.json` | Open positions, daily_pnl, total_pnl |
| `current_prices_cache.json` | Last fetched prices + candles |
| `historical_cache.json` | Full candle history per ticker |
| `trade_log.json` | All executed trades |

```python
def save_positions(data):
    with open('positions.json', 'w') as f:
        json.dump(data, f, indent=2)

def save_prices_cache(prices, candles_by_ticker):
    data = {
        'timestamp': datetime.now().isoformat(),
        'prices': prices,
        'candles': {
            t: [
                {'open': c['open'], 'high': c['high'],
                 'low': c['low'], 'close': c['close'],
                 'volume': c['volume'], 'datetime': c['datetime']}
                for c in candles
            ]
            for t, candles in candles_by_ticker.items()
        },
    }
    with open('current_prices_cache.json', 'w') as f:
        json.dump(data, f, indent=2)
```

**Pitfall:** Don't commit cache files to git. Add to `.gitignore`:
```
current_prices_cache.json
historical_cache.json
```

## Display Layout

### Layout checklist (match the mockup exactly)

When the user shares a visual mockup, match it exactly — do not impose your own layout guesses:

1. Panel order (top to bottom)
2. Which panels repeat (e.g. top + bottom status bar)
3. Title placement: left-aligned, right-aligned, centered, or as a panel title
4. Border color and text color (light gray vs bright)
5. Column structure (e.g. Symbol | Price | Chart | 7c)
6. Chart style: classic sparkline chars vs horizontal candle bars vs mini candle bars
7. Placeholder text and placeholder style ('N/A', '—', '-')
8. Spacing: number of blank lines between panels

### Example layout (this project's mockup)

```
<top box: "No open positions" — thin border, plain text>
<blank line>
<status bar: refresh in 3s • uptime Xs • ctrl+c quit>
<blank line>
<SCALPING BOT panel>
  SCALPING BOT          <- title (right-aligned or panel title)
  Cash: ... BP: ... Value: ... Day PnL: +X.XX   <- line 1
  Total PnL: +X.XX  YYYY-MM-DD HH:MM:SS          <- line 2
<blank line>
<BID/ASK table>
  Symbol | Price | Chart | 7c   <- headers
  /YM    | $X.XX | ███...   | -  <- rows (green bar in Chart, '-' in 7c)
  ...
<blank line>
<POSITIONS panel: header + thin box with '-' row + content>
<blank line>
<bottom status bar: refresh in 3s • uptime Xs • ctrl+c quit>
```

## Common Pitfalls

1. **Sparkline index error** — Always use `len(chars) - 1` in the index calculation.
2. **Rich Live with list** — `live.update([a, b, c])` fails. Use `Group(a, b, c)`.
3. **API rate limits** — 6 tickers × 2 API calls each = 12 calls per cycle. At 3-second cycles, that's 240 calls/minute. Schwab limit is ~120/min. Add small delays between calls or reduce ticker count.
4. **Stale token** — If API returns 401, token expired. Refresh or re-authenticate. See `references/tui-token-refresh.md`.
5. **No positions file** — Handle missing `positions.json` gracefully (start with empty positions).
6. **Terminal size** — Long sparklines or wide tables may wrap on small terminals. Keep tables compact.
7. **Stutter / flicker** — Reprinting panels one at a time (multiple `console.print()` calls) combines with `console.clear()` to produce visible flicker. Fix: single `Group` + single `clear()` + single `print(scene)`. See "Refresh Loop" above.
8. **Duplication (appearing to stack)** — Rich Live does NOT update in non-TTY contexts; it prints a full copy each refresh. Prefer unconditional clear+single-print. Diagnose by counting scene markers in a timed headless run.
9. **Mockup-driven layout** — Match the mockup exactly. Panel order, repeating panels, title alignment, colors, column structure, chart style, placeholders, spacing. Build what the mockup shows, not what you would have chosen.
