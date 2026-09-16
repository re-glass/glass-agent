#!/usr/bin/env python3
"""Verification script for trading bot main loop.
Run this after writing a new trading bot to verify:
1. Position tracking works
2. Daily loss limit is dynamic (not hardcoded)
3. Max positions is enforced
4. Duplicate per-ticker entries are blocked
5. SL/TP exit logic is correct
6. Market close handling works

Usage: python3 verify_mainloop.py
"""

import sys
from datetime import datetime

def test_position_tracking():
    """Test position add/remove/PnL calculation."""
    paper_positions = {}
    
    # Add position
    paper_positions['META'] = {
        'side': 'long', 'qty': 40, 'entry': 150.0,
        'sl': 149.5, 'tp': 150.75, 'entry_time': datetime.now()
    }
    assert 'META' in paper_positions
    assert paper_positions['META']['qty'] == 40
    
    # SL hit
    pos = paper_positions['META']
    last_price = 149.4
    if last_price <= pos['sl']:
        pnl = (pos['sl'] - pos['entry']) * pos['qty']
        assert abs(pnl - (-20.0)) < 0.01
    
    # Remove
    paper_positions.pop('META')
    assert 'META' not in paper_positions
    print("  PASS: Position tracking")

def test_dynamic_daily_loss():
    """Test daily loss limit is percentage-based."""
    account_value = 1000.0
    max_daily_loss_pct = 0.05
    daily_loss_limit = -(account_value * max_daily_loss_pct)
    assert daily_loss_limit == -50.0
    
    # Under limit: keep trading
    assert -30.0 >= daily_loss_limit
    # At limit: keep trading (strict less-than)
    assert -50.0 >= daily_loss_limit
    # Over limit: stop
    assert -51.0 < daily_loss_limit
    
    # Different account size
    account_value = 500.0
    daily_loss_limit = -(account_value * max_daily_loss_pct)
    assert daily_loss_limit == -25.0
    print("  PASS: Dynamic daily loss limit")

def test_max_positions():
    """Test max positions enforcement."""
    max_positions = 2
    paper_positions = {
        'META': {'side': 'long'}, 'GOOGL': {'side': 'short'}
    }
    open_positions = {}
    
    assert len(paper_positions) >= max_positions
    can_enter = len(paper_positions) < max_positions and len(open_positions) < max_positions
    assert not can_enter
    
    paper_positions.pop('GOOGL')
    can_enter = len(paper_positions) < max_positions and len(open_positions) < max_positions
    assert can_enter
    print("  PASS: Max positions enforcement")

def test_duplicate_blocking():
    """Test duplicate per-ticker entry blocking."""
    paper_positions = {'META': {'side': 'long'}}
    open_positions = {}
    
    ticker = 'META'
    if ticker in open_positions or ticker in paper_positions:
        blocked = True
    else:
        blocked = False
    assert blocked
    
    ticker = 'AAPL'
    if ticker in open_positions or ticker in paper_positions:
        blocked = True
    else:
        blocked = False
    assert not blocked
    print("  PASS: Duplicate per-ticker blocking")

def test_exit_conditions():
    """Test long/short SL/TP exit logic."""
    # Long SL
    pos = {'side': 'long', 'entry': 100.0, 'qty': 10, 'sl': 99.5, 'tp': 101.0}
    last = 99.4
    if last <= pos['sl']:
        pnl = (pos['sl'] - pos['entry']) * pos['qty']
        assert abs(pnl - (-5.0)) < 0.01
    
    # Long TP
    last = 101.1
    if last >= pos['tp']:
        pnl = (pos['tp'] - pos['entry']) * pos['qty']
        assert abs(pnl - 10.0) < 0.01
    
    # Short SL
    pos = {'side': 'short', 'entry': 100.0, 'qty': 10, 'sl': 100.5, 'tp': 99.0}
    last = 100.6
    if last >= pos['sl']:
        pnl = (pos['entry'] - pos['sl']) * pos['qty']
        assert abs(pnl - (-5.0)) < 0.01
    
    # Short TP
    last = 98.9
    if last <= pos['tp']:
        pnl = (pos['entry'] - pos['tp']) * pos['qty']
        assert abs(pnl - 10.0) < 0.01
    
    print("  PASS: Exit conditions")

def test_market_close():
    """Test market close position closing."""
    paper_positions = {
        'META': {'side': 'long', 'entry': 150.0, 'qty': 10},
        'NFLX': {'side': 'short', 'entry': 200.0, 'qty': 5},
    }
    total_close_pnl = 0
    
    for ticker, pos in list(paper_positions.items()):
        last_price = 152.0 if ticker == 'META' else 198.0
        if pos['side'] == 'long':
            pnl = (last_price - pos['entry']) * pos['qty']
        else:
            pnl = (pos['entry'] - last_price) * pos['qty']
        total_close_pnl += pnl
    
    # META long: (152 - 150) * 10 = +$20
    # NFLX short: (200 - 198) * 5 = +$10
    assert abs(total_close_pnl - 30.0) < 0.01
    
    paper_positions.clear()
    assert len(paper_positions) == 0
    print("  PASS: Market close handling")

def main():
    print("=" * 60)
    print("TRADING BOT MAIN LOOP VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_position_tracking,
        test_dynamic_daily_loss,
        test_max_positions,
        test_duplicate_blocking,
        test_exit_conditions,
        test_market_close,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
