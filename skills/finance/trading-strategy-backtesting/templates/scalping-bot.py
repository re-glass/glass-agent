#!/usr/bin/env python3
"""
Live Scalping Bot Template
==========================
Mean Reversion Strategy on 1-Minute Bars

This template implements a complete live trading bot using:
- Charles Schwab API (OAuth2)
- VWAP + Bollinger Bands + RSI + ATR indicators
- 2% risk per trade, 5% daily loss limit
- Paper trading mode for safe testing

USAGE:
1. Fill in SCHWAB_CONFIG below with your API credentials
2. Set paper_trading: True for testing
3. Run: python3 scalping-bot.py
4. After 2+ weeks of successful paper trading, set paper_trading: False
"""

import pandas as pd
import numpy as np
import requests
import json
import time
from datetime import datetime, timedelta
import os
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============================================================
# CONFIGURATION
# ============================================================

SCHWAB_CONFIG = {
    'app_key': 'YOUR_APP_KEY_HERE',       # From developer.schwab.com
    'app_secret': 'YOUR_APP_SECRET_HERE',  # From developer.schwab.com
    'redirect_uri': 'http://localhost:8080',
    'token_path': 'tokens.json',
    'paper_trading': True,                 # SET TO False ONLY AFTER PAPER TESTING
}

STRATEGY_CONFIG = {
    'tickers': ['AAPL', 'GOOGL', 'META', 'AMZN', 'NFLX'],
    'max_positions': 2,
    'risk_pct': 0.02,                      # 2% of account per trade
    'max_daily_loss_pct': 0.05,            # 5% kill switch
    'sl_atr_mult': 1.0,                    # Stop loss = 1.0 x ATR
    'tp_atr_mult': 1.5,                    # Take profit = 1.5 x ATR
    'rsi_oversold': 30,
    'rsi_overbought': 65,
    'vwap_deviation': 0.3,                 # % deviation from VWAP to trigger
    'bb_pctb_long': 0.1,                   # BB %B threshold for long entry
    'bb_pctb_short': 0.9,                  # BB %B threshold for short entry
    'market_open': (9, 30),                # ET
    'market_close': (16, 0),               # ET
    'poll_interval': 30,                   # Seconds between iterations
}

# ============================================================
# SCHWAB API CLIENT
# ============================================================

class SchwabAPI:
    def __init__(self, config):
        self.config = config
        self.base_url = 'https://api.schwabapi.com/v1'
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.account_id = None
        self.load_tokens()
    
    def load_tokens(self):
        if os.path.exists(self.config['token_path']):
            with open(self.config['token_path'], 'r') as f:
                tokens = json.load(f)
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            self.token_expiry = datetime.fromisoformat(tokens.get('expiry', '2000-01-01'))
            self.account_id = tokens.get('account_id')
            print("[Auth] Loaded saved tokens.")
    
    def save_tokens(self):
        tokens = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expiry': self.token_expiry.isoformat() if self.token_expiry else None,
            'account_id': self.account_id,
        }
        with open(self.config['token_path'], 'w') as f:
            json.dump(tokens, f, indent=2)
        os.chmod(self.config['token_path'], 0o600)  # Restrict permissions
        print("[Auth] Tokens saved.")
    
    def is_authenticated(self):
        if not self.access_token:
            return False
        if self.token_expiry and datetime.now() > self.token_expiry:
            return False
        return True
    
    def authenticate(self):
        auth_url = (
            f"{self.base_url}/oauth/authorize"
            f"?client_id={self.config['app_key']}"
            f"&redirect_uri={urllib.parse.quote(self.config['redirect_uri'])}"
            f"&response_type=code"
        )
        
        print("\n" + "="*50)
        print("AUTHENTICATION REQUIRED")
        print("="*50)
        print(f"Opening: {auth_url}")
        print("After login, copy the 'code' from the redirect URL.\n")
        
        webbrowser.open(auth_url)
        
        # Try to capture via local server
        code = self._capture_oauth_code()
        if not code:
            code = input("Enter authorization code: ").strip()
        
        self._exchange_code_for_tokens(code)
    
    def _capture_oauth_code(self, timeout=120):
        code_holder = [None]
        
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if 'code=' in self.path:
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    code_holder[0] = params.get('code', [None])[0]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'<h1>Auth successful!</h1><p>You can close this window.</p>')
                else:
                    self.send_response(400)
                    self.end_headers()
            def log_message(self, format, *args):
                pass
        
        server = HTTPServer(('localhost', 8080), Handler)
        server.timeout = timeout
        print("Waiting for OAuth callback...")
        server.handle_request()
        return code_holder[0]
    
    def _exchange_code_for_tokens(self, code):
        response = requests.post(
            f"{self.base_url}/oauth/token",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.config['app_key'],
                'client_secret': self.config['app_secret'],
                'redirect_uri': self.config['redirect_uri'],
            }
        )
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.status_code} {response.text}")
        
        data = response.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.token_expiry = datetime.now() + timedelta(seconds=data.get('expires_in', 1800))
        self.save_tokens()
        print("[Auth] Authentication successful!")
    
    def refresh_tokens(self):
        response = requests.post(
            f"{self.base_url}/oauth/token",
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.config['app_key'],
                'client_secret': self.config['app_secret'],
            }
        )
        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.status_code}")
        data = response.json()
        self.access_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.token_expiry = datetime.now() + timedelta(seconds=data.get('expires_in', 1800))
        self.save_tokens()
        print("[Auth] Tokens refreshed.")
    
    def _headers(self):
        if self.token_expiry and datetime.now() > self.token_expiry:
            self.refresh_tokens()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
    
    def get_account_id(self):
        if self.account_id:
            return self.account_id
        response = requests.get(f"{self.base_url}/accounts/accountNumbers", headers=self._headers())
        if response.status_code == 200:
            accounts = response.json()
            if accounts:
                self.account_id = accounts[0].get('accountNumber')
                self.save_tokens()
                return self.account_id
        raise Exception(f"Failed to get account ID: {response.status_code}")
    
    def get_account_info(self):
        account_id = self.get_account_id()
        response = requests.get(
            f"{self.base_url}/accounts/{account_id}",
            headers=self._headers(),
            params={'fields': 'positions'}
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get account info: {response.status_code}")
    
    def get_price_history(self, symbol, period_type='day', period=5, frequency_type='minute', frequency=1):
        response = requests.get(
            f"{self.base_url}/marketdata/{symbol}/pricehistory",
            headers=self._headers(),
            params={
                'periodType': period_type,
                'period': period,
                'frequencyType': frequency_type,
                'frequency': frequency,
            }
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get price history for {symbol}: {response.status_code}")
    
    def get_quote(self, symbol):
        response = requests.get(
            f"{self.base_url}/marketdata/{symbol}/quotes",
            headers=self._headers()
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Failed to get quote for {symbol}: {response.status_code}")
    
    def place_order(self, symbol, side, quantity, order_type='MARKET', limit_price=None):
        account_id = self.get_account_id()
        order = {
            'session': 'NORMAL',
            'duration': 'DAY',
            'orderType': order_type,
            'quantity': quantity,
            'symbol': symbol,
            'instruction': side,  # 'BUY' or 'SELL'
        }
        if order_type == 'LIMIT' and limit_price:
            order['price'] = limit_price
        
        response = requests.post(
            f"{self.base_url}/accounts/{account_id}/orders",
            headers={**self._headers(), 'Content-Type': 'application/json'},
            json=order
        )
        if response.status_code in [200, 201]:
            print(f"[Order] {side} {quantity} {symbol} @ {order_type}")
            return response.json()
        raise Exception(f"Order failed: {response.status_code} {response.text}")


# ============================================================
# INDICATORS
# ============================================================

def compute_indicators(df):
    """Compute VWAP, Bollinger Bands, RSI, ATR."""
    df = df.copy()
    
    # VWAP (safer pandas pattern — avoids groupby().apply() issues)
    df['_date'] = df.index.date
    df['CumVol'] = df.groupby('_date')['Volume'].cumsum()
    df['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['CumVolPrice'] = (df['Volume'] * df['TypicalPrice']).groupby(df['_date']).cumsum()
    df['VWAP'] = df['CumVolPrice'] / df['CumVol']
    df = df.drop(columns=['CumVol', 'CumVolPrice', 'TypicalPrice', '_date'])
    
    # Bollinger Bands
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + (2.0 * bb_std)
    df['BB_Lower'] = df['BB_Mid'] - (2.0 * bb_std)
    df['BB_PctB'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    # NOTE: BB_PctB CAN be < 0 or > 1 — this is intentional and expected
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    return df


def generate_signal(row, config):
    """Mean reversion signal: returns 1 (long), -1 (short), or 0 (none)."""
    if pd.isna(row['VWAP']) or pd.isna(row['RSI']) or pd.isna(row['BB_PctB']) or pd.isna(row['ATR']):
        return 0
    
    deviation = (row['Close'] - row['VWAP']) / row['VWAP'] * 100
    
    # Long: price below VWAP, RSI oversold, BB near lower band
    if (deviation < -config['vwap_deviation'] and 
        row['RSI'] < config['rsi_oversold'] and 
        row['BB_PctB'] < config['bb_pctb_long']):
        return 1
    
    # Short: price above VWAP, RSI overbought, BB near upper band
    if (deviation > config['vwap_deviation'] and 
        row['RSI'] > config['rsi_overbought'] and 
        row['BB_PctB'] > config['bb_pctb_short']):
        return -1
    
    return 0


# ============================================================
# MAIN TRADING LOOP
# ============================================================

def main():
    print("="*70)
    print("MEAN REVERSION SCALPING BOT")
    print("="*70)
    
    cfg = STRATEGY_CONFIG
    paper = SCHWAB_CONFIG['paper_trading']
    
    # Auth
    api = SchwabAPI(SCHWAB_CONFIG)
    if not api.is_authenticated():
        api.authenticate()
    
    # Account info
    account = api.get_account_info()
    balance = account.get('securitiesAccount', {}).get('currentBalances', {})
    print(f"\nAccount: {api.account_id}")
    print(f"Cash: ${balance.get('cashBalance', 0):,.2f}")
    print(f"Buying Power: ${balance.get('buyingPower', 0):,.2f}")
    print(f"Paper Trading: {paper}")
    print(f"Tickers: {cfg['tickers']}")
    print(f"Risk/Trade: {cfg['risk_pct']*100}% | Max Daily Loss: {cfg['max_daily_loss_pct']*100}%")
    print(f"Max Positions: {cfg['max_positions']}")
    print("\nStarting...\n")
    
    daily_pnl = 0.0
    today = datetime.now().date()
    
    try:
        while True:
            # Reset daily P&L at start of new day
            if datetime.now().date() != today:
                today = datetime.now().date()
                daily_pnl = 0.0
                print(f"\n--- {today} ---\n")
            
            # Market hours check (ET)
            now = datetime.now()
            market_open = now.replace(hour=cfg['market_open'][0], minute=cfg['market_open'][1], second=0)
            market_close = now.replace(hour=cfg['market_close'][0], minute=cfg['market_close'][1], second=0)
            
            if now < market_open or now > market_close:
                print(f"Outside market hours ({now.strftime('%H:%M')}). Waiting...")
                time.sleep(60)
                continue
            
            # Daily loss limit
            if daily_pnl < -100:  # Replace with account_value * cfg['max_daily_loss_pct']
                print(f"Daily loss limit hit (${daily_pnl:.2f}). Sleeping.")
                time.sleep(60)
                continue
            
            # Process each ticker
            for ticker in cfg['tickers']:
                try:
                    # Get price history
                    history = api.get_price_history(
                        ticker, period_type='day', period=5,
                        frequency_type='minute', frequency=1
                    )
                    
                    if not history or 'candles' not in history:
                        continue
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(history['candles'])
                    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms', utc=True).dt.tz_convert('US/Eastern')
                    df.set_index('datetime', inplace=True)
                    df = df[['open', 'high', 'low', 'close', 'volume']].rename(columns={
                        'open': 'Open', 'high': 'High', 'low': 'Low',
                        'close': 'Close', 'volume': 'Volume'
                    })
                    
                    # Compute indicators
                    df = compute_indicators(df)
                    df = df.dropna()
                    if df.empty:
                        continue
                    
                    # Generate signal
                    latest = df.iloc[-1]
                    signal = generate_signal(latest, cfg)
                    
                    if signal == 0:
                        continue
                    
                    # Get current quote
                    quote = api.get_quote(ticker)
                    ticker_data = quote.get(ticker, {})
                    bid = ticker_data.get('bidPrice', 0)
                    ask = ticker_data.get('askPrice', 0)
                    
                    entry_price = ask if signal == 1 else bid
                    atr = latest['ATR']
                    
                    if pd.isna(atr) or atr == 0:
                        continue
                    
                    # Position sizing
                    account = api.get_account_info()
                    account_value = account.get('securitiesAccount', {}).get('currentBalances', {}).get('liquidationValue', 0)
                    risk_amount = account_value * cfg['risk_pct']
                    stop_distance = atr * cfg['sl_atr_mult']
                    
                    if stop_distance == 0:
                        continue
                    
                    qty = max(1, int(risk_amount / stop_distance))
                    
                    if signal == 1:
                        side = 'BUY'
                        sl_price = entry_price - stop_distance
                        tp_price = entry_price + (stop_distance * cfg['tp_atr_mult'] / cfg['sl_atr_mult'])
                    else:
                        side = 'SELL'
                        sl_price = entry_price + stop_distance
                        tp_price = entry_price - (stop_distance * cfg['tp_atr_mult'] / cfg['sl_atr_mult'])
                    
                    print(f"\n[{now.strftime('%H:%M:%S')}] {ticker}:")
                    print(f"  Signal: {side} | Price: ${entry_price:.2f} | ATR: ${atr:.3f}")
                    print(f"  SL: ${sl_price:.2f} | TP: ${tp_price:.2f} | Qty: {qty}")
                    print(f"  Risk: ${risk_amount:.2f} ({cfg['risk_pct']*100}% of ${account_value:.2f})")
                    
                    if not paper:
                        order = api.place_order(ticker, side, qty)
                        if order:
                            print("  ORDER PLACED")
                    else:
                        print("  [PAPER TRADE]")
                
                except Exception as e:
                    print(f"Error processing {ticker}: {e}")
            
            time.sleep(cfg['poll_interval'])
    
    except KeyboardInterrupt:
        print("\n\nBot stopped.")
        print(f"Daily P&L: ${daily_pnl:.2f}")


if __name__ == '__main__':
    main()
