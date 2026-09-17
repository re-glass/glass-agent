#!/usr/bin/env python3
"""Non-blocking verification of gui/app.py: syntax, routes, scene_html output,
mockup-layout tokens, data loading. Avoids launching webview window (blocks).
"""
import sys, os, ast
from pathlib import Path

BASE = Path('/home/reg/scalping_bot')
GUI = BASE / 'gui' / 'app.py'
VENVPK = BASE / 'venv' / 'lib' / 'python3.14' / 'site-packages'

results = []
def check(name, ok, detail=''):
    results.append(bool(ok))
    tag = 'PASS' if ok else 'FAIL'
    print(f'[{tag}] {name}' + (f'  -- {detail}' if detail else ''))

# Syntax
try:
    ast.parse(GUI.read_text(encoding='utf-8'))
    check('AST syntax OK', True)
except SyntaxError as e:
    check('AST syntax OK', False, str(e))
    sys.exit(1)

src = GUI.read_text(encoding='utf-8')

# Required symbols
for tok in ['TICKERS', 'scene_html', 'price_html', 'positions_html',
            'import webview', 'signal.signal', 'atexit.register',
            'FALLBACK_SHELL']:
    check(f'has: {tok}', tok in src, tok)

# price_html signature (ticker-first)
check('price_html(ticker,...)', 'def price_html(ticker, price, max_price):' in src)

# No leftover Jinja
check('no {{ placeholders', '{{' not in src)

# Layout tokens (mockup match)
layout = ['top-box', 'SCALPING BOT', 'Cash:', 'BP:', 'Value:', 'Day PnL:',
           'Total PnL:', 'BID/ASK', 'POSITIONS', 'refresh in 3s', 'ctrl+c quit',
           'candle', 'bar-fill', '#5a7a9a', '#7ec8e3', '#0a0a12']
for tok in layout:
    check(f'layout: {tok}', tok in src, tok)

# All tickers
for t in ['/YM', '/GC', '/ES', '/NQ', '/CL', '/SI']:
    check(f'ticker {t}', t in src, t)

# Runtime: import + scene_html
sys.path.insert(0, str(VENVPK))
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))
try:
    import gui.app as g
    html = g.scene_html()
    check('scene_html() runs', True)
    check('fragment has SCALPING BOT', 'SCALPING BOT' in html)
    check('fragment has all tickers',
          all(t in html for t in ['/YM','/GC','/ES','/NQ','/CL','/SI']))
    check('fragment has chart markup', 'bar-fill' in html or 'candle' in html)
    check('fragment no {{', '{{' not in html)
    rules = [str(r) for r in g.APP.url_map.iter_rules()]
    check('route /', '/' in rules)
    check('route /api/scene', '/api/scene' in rules)
except Exception as e:
    check(f'GUI import + scene_html', False, f'{type(e).__name__}: {e}')

passed = sum(results)
total = len(results)
print(f'\nSUMMARY: {passed}/{total} passed')
sys.exit(0 if passed == total else 1)
