#!/usr/bin/env python3
"""Verify Schwab API connectivity and diagnose 404 errors.

Usage:
    python3 scripts/verify_connection.py
    
This script tests all major endpoints and reports which are working.
Run this when getting 404 errors to diagnose the cause.
"""
import requests
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_token():
    """Load token from tokens.json."""
    token_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tokens.json')
    if not os.path.exists(token_path):
        print("ERROR: tokens.json not found. Run the bot first to authenticate.")
        sys.exit(1)
    with open(token_path) as f:
        return json.load(f)['access_token']

def test_endpoint(name, method, url, headers, params=None):
    """Test an endpoint and report status."""
    try:
        resp = requests.request(method, url, headers=headers, params=params, timeout=10)
        status = "PASS" if resp.status_code == 200 else "FAIL"
        body = resp.text[:200] if resp.text else "(empty)"
        print(f"[{status}] {name}")
        print(f"  URL: {url}")
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {body}")
        print()
        return resp.status_code == 200
    except Exception as e:
        print(f"[ERROR] {name}")
        print(f"  URL: {url}")
        print(f"  Error: {e}")
        print()
        return False

def main():
    token = load_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    print("=" * 60)
    print("SCHWAB API CONNECTION DIAGNOSTIC")
    print("=" * 60)
    print(f"Token (first 30): {token[:30]}...")
    print()
    
    results = []
    
    # Test 1: Account Numbers (Trader API)
    results.append(test_endpoint(
        "Account Numbers",
        "GET",
        "https://api.schwabapi.com/trader/v1/accounts/accountNumbers",
        headers
    ))
    
    # Test 2: AAPL Quotes (Market Data API)
    results.append(test_endpoint(
        "AAPL Quotes",
        "GET",
        "https://api.schwabapi.com/marketdata/v1/AAPL/quotes",
        headers
    ))
    
    # Test 3: AAPL Price History (Market Data API)
    results.append(test_endpoint(
        "AAPL Price History",
        "GET",
        "https://api.schwabapi.com/marketdata/v1/pricehistory",
        headers,
        params={
            'symbol': 'AAPL',
            'periodType': 'day',
            'period': 1,
            'frequencyType': 'minute',
            'frequency': 1
        }
    ))
    
    # Summary
    print("=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} endpoints working")
    print("=" * 60)
    
    if all(results):
        print("All endpoints working! The bot should function correctly.")
    elif not results[0]:
        print("Account endpoint failing — check base URL is /trader/v1")
    elif not results[1] or not results[2]:
        print("Market data endpoints failing — provisioning may still be pending")
    
    return 0 if all(results) else 1

if __name__ == '__main__':
    sys.exit(main())
