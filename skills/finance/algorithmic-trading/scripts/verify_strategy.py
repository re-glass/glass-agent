#!/usr/bin/env python3
"""
Ad-hoc Verification Template for Trading Strategy Code
Usage: python scripts/verify_strategy.py
Copy this file into your project and customize the tests.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys

# Import your strategy functions
# from live_bot import compute_indicators, generate_signal

# ============================================================
# TEST 1: Indicator Calculations
# ============================================================

def test_compute_indicators():
    """Test that indicators are calculated correctly."""
    print("TEST 1: compute_indicators()")
    
    # Create sample 1-min data
    np.random.seed(42)
    n = 390  # One trading day
    base_price = 150.0
    prices = base_price + np.cumsum(np.random.randn(n) * 0.1)
    
    dates = pd.date_range('2026-09-10 09:30', periods=n, freq='1min', tz='US/Eastern')
    df = pd.DataFrame({
        'Open': prices + np.random.randn(n) * 0.05,
        'High': prices + abs(np.random.randn(n) * 0.1),
        'Low': prices - abs(np.random.randn(n) * 0.1),
        'Close': prices + np.random.randn(n) * 0.05,
        'Volume': np.random.randint(1000, 50000, n),
    }, index=dates)
    
    result = compute_indicators(df)
    
    # Verify all indicators exist
    for col in ['VWAP', 'BB_Mid', 'BB_Upper', 'BB_Lower', 'BB_PctB', 'RSI', 'ATR']:
        assert col in result.columns, f"{col} missing"
    
    # Verify VWAP is reasonable
    valid_vwap = result['VWAP'].dropna()
    assert len(valid_vwap) > 0, "VWAP all NaN"
    assert valid_vwap.between(base_price - 10, base_price + 10).all(), "VWAP far from price"
    
    # Verify BB_PctB is valid (can be <0 or >1)
    valid_bb = result['BB_PctB'].dropna()
    assert len(valid_bb) > 0, "BB_PctB all NaN"
    
    # Verify RSI is in valid range
    valid_rsi = result['RSI'].dropna()
    assert len(valid_rsi) > 0, "RSI all NaN"
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all(), "RSI out of [0,100]"
    
    # Verify ATR is positive
    valid_atr = result['ATR'].dropna()
    assert len(valid_atr) > 0, "ATR all NaN"
    assert (valid_atr > 0).all(), "ATR should be positive"
    
    print("  PASSED")
    return True


# ============================================================
# TEST 2: Signal Generation
# ============================================================

def test_generate_signal():
    """Test signal logic with known inputs."""
    print("TEST 2: generate_signal()")
    
    # LONG signal: price below VWAP, RSI < 30, BB < 0.1
    row_long = pd.Series({
        'Close': 148.0,
        'VWAP': 150.0,  # deviation = -1.33%
        'RSI': 25.0,
        'BB_PctB': 0.05,
        'ATR': 0.5,
    })
    sig = generate_signal(row_long)
    assert sig == 1, f"Expected LONG (1), got {sig}"
    
    # SHORT signal: price above VWAP, RSI > 65, BB > 0.9
    row_short = pd.Series({
        'Close': 152.0,
        'VWAP': 150.0,  # deviation = +1.33%
        'RSI': 75.0,
        'BB_PctB': 0.95,
        'ATR': 0.5,
    })
    sig = generate_signal(row_short)
    assert sig == -1, f"Expected SHORT (-1), got {sig}"
    
    # NO signal: neutral conditions
    row_neutral = pd.Series({
        'Close': 150.05,
        'VWAP': 150.0,
        'RSI': 50.0,
        'BB_PctB': 0.5,
        'ATR': 0.5,
    })
    sig = generate_signal(row_neutral)
    assert sig == 0, f"Expected NONE (0), got {sig}"
    
    # NO signal: missing data
    row_missing = pd.Series({
        'Close': 150.0,
        'VWAP': np.nan,
        'RSI': 25.0,
        'BB_PctB': 0.05,
        'ATR': 0.5,
    })
    sig = generate_signal(row_missing)
    assert sig == 0, f"Expected NONE (0) for NaN VWAP, got {sig}"
    
    # Boundary: RSI exactly 30 (not < 30)
    row_boundary = pd.Series({
        'Close': 148.0,
        'VWAP': 150.0,
        'RSI': 30.0,  # NOT < 30
        'BB_PctB': 0.05,
        'ATR': 0.5,
    })
    sig = generate_signal(row_boundary)
    assert sig == 0, f"Expected NONE (0) for RSI=30, got {sig}"
    
    print("  PASSED")
    return True


# ============================================================
# TEST 3: Position Sizing
# ============================================================

def test_position_sizing():
    """Test 2% risk position sizing."""
    print("TEST 3: Position sizing logic")
    
    account_value = 1000.0
    risk_pct = 0.02
    atr = 0.5
    sl_mult = 1.0
    
    risk_amount = account_value * risk_pct  # $20
    stop_distance = atr * sl_mult  # $0.50
    qty = max(1, int(risk_amount / stop_distance))  # 40
    
    assert qty == 40, f"Expected qty=40, got {qty}"
    actual_risk = qty * stop_distance
    assert abs(actual_risk - risk_amount) < stop_distance, "Risk not within 1 stop distance"
    
    # Large ATR (qty should be at least 1)
    atr_large = 100.0
    qty_large = max(1, int(risk_amount / (atr_large * sl_mult)))
    assert qty_large == 1, f"Expected qty=1 for large ATR, got {qty_large}"
    
    print("  PASSED")
    return True


# ============================================================
# TEST 4: Daily Loss Limit
# ============================================================

def test_daily_loss_limit():
    """Test 5% daily kill switch."""
    print("TEST 4: Daily loss limit (kill switch)")
    
    account_value = 1000.0
    max_daily_loss_pct = 0.05
    daily_loss_limit = -account_value * max_daily_loss_pct  # -$50
    
    # Under limit
    daily_pnl = -30.0
    assert daily_pnl >= daily_loss_limit, "Should NOT trigger at -$30"
    
    # At limit (still trading)
    daily_pnl = -50.0
    assert daily_pnl >= daily_loss_limit, "Should NOT trigger exactly at -$50"
    
    # Over limit
    daily_pnl = -51.0
    assert daily_pnl < daily_loss_limit, "Should trigger at -$51"
    
    print("  PASSED")
    return True


# ============================================================
# TEST 5: SL/TP Price Calculation
# ============================================================

def test_sl_tp_prices():
    """Test stop loss and take profit price calculations."""
    print("TEST 5: SL/TP price calculation")
    
    entry_price = 150.0
    atr = 0.5
    sl_mult = 1.0
    tp_mult = 1.5
    stop_distance = atr * sl_mult
    
    # Long
    long_sl = entry_price - stop_distance
    long_tp = entry_price + (stop_distance * tp_mult / sl_mult)
    assert abs(long_sl - 149.50) < 0.001, f"Long SL wrong: {long_sl}"
    assert abs(long_tp - 150.75) < 0.001, f"Long TP wrong: {long_tp}"
    
    # Short
    short_sl = entry_price + stop_distance
    short_tp = entry_price - (stop_distance * tp_mult / sl_mult)
    assert abs(short_sl - 150.50) < 0.001, f"Short SL wrong: {short_sl}"
    assert abs(short_tp - 149.25) < 0.001, f"Short TP wrong: {short_tp}"
    
    # Reward-to-risk ratio
    rr = (long_tp - entry_price) / (entry_price - long_sl)
    assert abs(rr - 1.5) < 0.001, f"R:R should be 1.5, got {rr}"
    
    print("  PASSED")
    return True


# ============================================================
# RUN ALL TESTS
# ============================================================

def main():
    print("=" * 60)
    print("AD-HOC VERIFICATION")
    print("=" * 60)
    print()
    
    tests = [
        test_compute_indicators,
        test_generate_signal,
        test_position_sizing,
        test_daily_loss_limit,
        test_sl_tp_prices,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
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
