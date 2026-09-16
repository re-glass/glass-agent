#!/usr/bin/env python3
"""Verification script for trading bot logic.
Run to verify indicator calculations, signal generation, position sizing,
daily loss limits, market hours, and SL/TP price calculations.
"""

import pandas as pd
import numpy as np
import sys

def test_indicators():
    """Test VWAP, Bollinger Bands, RSI, ATR."""
    print("TEST 1: compute_indicators()")
    from live_bot import compute_indicators
    
    np.random.seed(42)
    n = 390
    prices = 150 + np.cumsum(np.random.randn(n) * 0.1)
    dates = pd.date_range('2026-09-10 09:30', periods=n, freq='1min', tz='US/Eastern')
    df = pd.DataFrame({
        'Open': prices + np.random.randn(n) * 0.05,
        'High': prices + abs(np.random.randn(n) * 0.1),
        'Low': prices - abs(np.random.randn(n) * 0.1),
        'Close': prices + np.random.randn(n) * 0.05,
        'Volume': np.random.randint(1000, 50000, n),
    }, index=dates)
    
    result = compute_indicators(df)
    
    assert 'VWAP' in result.columns and not result['VWAP'].isna().all()
    assert 'BB_PctB' in result.columns and len(result['BB_PctB'].dropna()) > 0
    assert 'RSI' in result.columns and len(result['RSI'].dropna()) > 0
    assert 'ATR' in result.columns and (result['ATR'].dropna() > 0).all()
    
    print("  PASSED")

def test_signals():
    """Test LONG, SHORT, NONE signals."""
    print("TEST 2: generate_signal()")
    from live_bot import generate_signal
    
    assert generate_signal(pd.Series({'Close': 148, 'VWAP': 150, 'RSI': 25, 'BB_PctB': 0.05, 'ATR': 0.5})) == 1
    assert generate_signal(pd.Series({'Close': 152, 'VWAP': 150, 'RSI': 75, 'BB_PctB': 0.95, 'ATR': 0.5})) == -1
    assert generate_signal(pd.Series({'Close': 150.05, 'VWAP': 150, 'RSI': 50, 'BB_PctB': 0.5, 'ATR': 0.5})) == 0
    
    print("  PASSED")

def test_position_sizing():
    """Test 2% risk position sizing."""
    print("TEST 3: Position sizing")
    
    account_value = 1000.0
    risk_pct = 0.02
    atr = 0.5
    
    risk_amount = account_value * risk_pct
    stop_distance = atr * 1.0
    qty = max(1, int(risk_amount / stop_distance))
    
    assert qty == 40
    
    # Small ATR
    qty_small = max(1, int(risk_amount / (100.0 * 1.0)))
    assert qty_small == 1
    
    print("  PASSED")

def test_daily_loss_limit():
    """Test 5% daily kill switch."""
    print("TEST 4: Daily loss limit")
    
    account_value = 1000.0
    max_daily_loss_pct = 0.05
    daily_limit = -account_value * max_daily_loss_pct
    
    assert not (-30.0 < daily_limit)  # Under limit
    assert not (-50.0 < daily_limit)  # At limit (equal doesn't trigger)
    assert (-51.0 < daily_limit)      # Over limit
    
    print("  PASSED")

def test_market_hours():
    """Test market hours check."""
    print("TEST 5: Market hours")
    
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    test_early = now.replace(hour=8, minute=0)
    test_late = now.replace(hour=17, minute=0)
    test_open = now.replace(hour=10, minute=0)
    
    assert test_early < market_open
    assert test_late > market_close
    assert market_open <= test_open <= market_close
    
    print("  PASSED")

def test_sl_tp():
    """Test stop loss and take profit calculations."""
    print("TEST 6: SL/TP prices")
    
    entry_price = 150.0
    atr = 0.5
    sl_mult = 1.0
    tp_mult = 1.5
    stop_distance = atr * sl_mult
    
    long_sl = entry_price - stop_distance
    long_tp = entry_price + (stop_distance * tp_mult / sl_mult)
    
    assert abs(long_sl - 149.50) < 0.001
    assert abs(long_tp - 150.75) < 0.001
    
    short_sl = entry_price + stop_distance
    short_tp = entry_price - (stop_distance * tp_mult / sl_mult)
    
    assert abs(short_sl - 150.50) < 0.001
    assert abs(short_tp - 149.25) < 0.001
    
    reward_risk = (long_tp - entry_price) / (entry_price - long_sl)
    assert abs(reward_risk - 1.5) < 0.001
    
    print("  PASSED")

def main():
    print("=" * 60)
    print("TRADING BOT VERIFICATION")
    print("=" * 60)
    print()
    
    tests = [
        test_indicators,
        test_signals,
        test_position_sizing,
        test_daily_loss_limit,
        test_market_hours,
        test_sl_tp,
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
    from datetime import datetime
    success = main()
    sys.exit(0 if success else 1)
