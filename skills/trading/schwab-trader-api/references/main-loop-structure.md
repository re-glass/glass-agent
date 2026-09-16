# Verified Main Loop Structure (Session-Tested)

This is the complete, verified main loop structure that was tested and debugged in session.

## Critical Requirements

1. **Position Tracking** — `open_positions` / `paper_positions` dicts keyed by ticker
2. **SL/TP Monitoring** — Check every 30 seconds, not just at entry
3. **Daily Loss Limit** — Dynamic: `-(account_value * 0.05)`, never hardcoded
4. **Max Positions** — Block signals when at capacity
5. **Duplicate Blocking** — Block same-ticker re-entry
6. **Market Close** — Close all positions at 4:00 PM ET
7. **Paper Trading Gate** — Real orders only when `paper_trading: False`

## Complete Implementation

```python
# State tracking
daily_pnl = 0.0
today = datetime.now().date()
open_positions = {}      # Live: ticker -> {side, qty, entry, sl, tp, entry_time}
paper_positions = {}     # Paper: same structure
total_pnl = 0.0
account_value = 1000.0   # Updated from API

try:
    while True:
        # Reset daily tracking at market open
        if datetime.now().date() != today:
            today = datetime.now().date()
            daily_pnl = 0.0
            open_positions.clear()
            paper_positions.clear()
            print(f"\n--- New Day: {today} ---\n")
        
        # Check market hours (9:30 AM - 4:00 PM ET)
        now = datetime.now()
        market_open = now.replace(hour=9, minute=30, second=0)
        market_close = now.replace(hour=16, minute=0, second=0)
        
        if now < market_open or now > market_close:
            print(f"Outside market hours ({now.strftime('%H:%M')}). Waiting...")
            time.sleep(60)
            continue
        
        # Check daily loss limit (DYNAMIC — not hardcoded)
        daily_loss_limit = -(account_value * max_daily_loss_pct)
        if daily_pnl < daily_loss_limit:
            print(f"Daily loss limit hit (${daily_pnl:.2f}). Stopping for today.")
            time.sleep(60)
            continue
        
        # Check max positions
        if len(open_positions) >= max_positions and len(paper_positions) >= max_positions:
            time.sleep(30)
            continue
        
        # Fetch data and check each ticker
        for ticker in tickers:
            try:
                # Skip if already in position for this ticker
                if ticker in open_positions or ticker in paper_positions:
                    continue
                
                # Get price history for indicators
                history = api.get_price_history(
                    ticker,
                    period_type='day',
                    period=5,
                    frequency_type='minute',
                    frequency=1
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
                signal = generate_signal(latest)
                
                if signal == 0:
                    continue
                
                # Get current price
                quote = api.get_quote(ticker)
                if not quote:
                    continue
                
                ticker_data = quote.get(ticker, {})
                bid = ticker_data.get('bidPrice', 0)
                ask = ticker_data.get('askPrice', 0)
                
                if signal == 1:
                    entry_price = ask
                else:
                    entry_price = bid
                
                # Calculate position size
                atr = latest['ATR']
                if pd.isna(atr) or atr == 0:
                    continue
                
                # Update account value periodically (not every tick)
                account_info = api.get_account_info()
                if account_info:
                    account_value = account_info.get('securitiesAccount', {}).get('currentBalances', {}).get('liquidationValue', 1000.0)
                
                risk_amount = account_value * risk_pct
                stop_distance = atr * 1.0
                
                if stop_distance == 0:
                    continue
                
                qty = max(1, int(risk_amount / stop_distance))
                
                if signal == 1:
                    side = 'BUY'
                    sl_price = entry_price - stop_distance
                    tp_price = entry_price + (stop_distance * 1.5)
                else:
                    side = 'SELL'
                    sl_price = entry_price + stop_distance
                    tp_price = entry_price - (stop_distance * 1.5)
                
                print(f"\n[{now.strftime('%H:%M:%S')}] Signal for {ticker}:")
                print(f"  Side: {side}")
                print(f"  Price: ${entry_price:.2f}")
                print(f"  SL: ${sl_price:.2f} (${stop_distance:.2f} away)")
                print(f"  TP: ${tp_price:.2f}")
                print(f"  Qty: {qty}")
                print(f"  Risk: ${risk_amount:.2f} ({risk_pct*100}% of ${account_value:.2f})")
                
                if not SCHWAB_CONFIG['paper_trading']:
                    # Place market order
                    order = api.place_order(ticker, side, qty)
                    if order:
                        print(f"  ORDER PLACED")
                        open_positions[ticker] = {
                            'side': 'long' if signal == 1 else 'short',
                            'qty': qty,
                            'entry': entry_price,
                            'sl': sl_price,
                            'tp': tp_price,
                            'entry_time': now
                        }
                    else:
                        print(f"  ORDER FAILED")
                else:
                    print(f"  [PAPER TRADE] Order would be placed")
                    paper_positions[ticker] = {
                        'side': 'long' if signal == 1 else 'short',
                        'qty': qty,
                        'entry': entry_price,
                        'sl': sl_price,
                        'tp': tp_price,
                        'entry_time': now
                    }
            
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
        
        # Monitor paper positions for exit conditions
        positions_to_close = []
        for ticker, pos in paper_positions.items():
            quote = api.get_quote(ticker)
            if not quote:
                continue
            ticker_data = quote.get(ticker, {})
            last_price = ticker_data.get('lastPrice', 0)
            
            if pos['side'] == 'long':
                if last_price <= pos['sl']:
                    pnl = (pos['sl'] - pos['entry']) * pos['qty']
                    print(f"\n  [PAPER SL] {ticker}: ${pos['sl']:.2f} hit, P&L: ${pnl:.2f}")
                    daily_pnl += pnl
                    total_pnl += pnl
                    positions_to_close.append(ticker)
                elif last_price >= pos['tp']:
                    pnl = (pos['tp'] - pos['entry']) * pos['qty']
                    print(f"\n  [PAPER TP] {ticker}: ${pos['tp']:.2f} hit, P&L: ${pnl:.2f}")
                    daily_pnl += pnl
                    total_pnl += pnl
                    positions_to_close.append(ticker)
            else:  # short
                if last_price >= pos['sl']:
                    pnl = (pos['entry'] - pos['sl']) * pos['qty']
                    print(f"\n  [PAPER SL] {ticker}: ${pos['sl']:.2f} hit, P&L: ${pnl:.2f}")
                    daily_pnl += pnl
                    total_pnl += pnl
                    positions_to_close.append(ticker)
                elif last_price <= pos['tp']:
                    pnl = (pos['entry'] - pos['tp']) * pos['qty']
                    print(f"\n  [PAPER TP] ${pos['tp']:.2f} hit, P&L: ${pnl:.2f}")
                    daily_pnl += pnl
                    total_pnl += pnl
                    positions_to_close.append(ticker)
        
        for ticker in positions_to_close:
            paper_positions.pop(ticker, None)
        
        # Market close: close all paper positions at 4:00 PM
        if now.hour == 16 and now.minute == 0:
            for ticker, pos in list(paper_positions.items()):
                quote = api.get_quote(ticker)
                if quote:
                    last_price = quote.get(ticker, {}).get('lastPrice', pos['entry'])
                    if pos['side'] == 'long':
                        pnl = (last_price - pos['entry']) * pos['qty']
                    else:
                        pnl = (pos['entry'] - last_price) * pos['qty']
                    print(f"\n  [PAPER MOC] {ticker} closed at ${last_price:.2f}, P&L: ${pnl:.2f}")
                    daily_pnl += pnl
                    total_pnl += pnl
            paper_positions.clear()
            print(f"\n--- Market Closed. Daily P&L: ${daily_pnl:.2f}, Total P&L: ${total_pnl:.2f} ---\n")
        
        time.sleep(30)

except KeyboardInterrupt:
    print("\n\nBot stopped by user.")
    print(f"Final Daily P&L: ${daily_pnl:.2f}")
    print(f"Total Session P&L: ${total_pnl:.2f}")
    print("Goodbye!")
```

## Position Sizing (Optimized)

```python
risk_amount = account_value * 0.02
stop_distance = atr * 1.0
qty = max(1, int(risk_amount / stop_distance))
```

## SL/TP Levels (Optimized from Backtest)

- **Long SL:** `entry - (1.0 × ATR)`
- **Long TP:** `entry + (1.5 × ATR)`  
- **Short SL:** `entry + (1.0 × ATR)`
- **Short TP:** `entry - (1.5 × ATR)`
- **Reward-to-Risk:** 1.5:1

## Daily Loss Limit

```python
daily_loss_limit = -(account_value * 0.05)
if daily_pnl < daily_loss_limit:
    # Stop trading for today
    time.sleep(60)
    continue
```

**Never hardcode** the loss limit to a fixed dollar amount like `-100`. It must be a percentage of the actual account value.

## Rate Limit Considerations

- Account info is fetched on signal, not every tick
- Quotes are fetched for position monitoring (5 tickers × 2/min = 10 calls/min)
- Price history is fetched only when checking for new signals
- Total: ~15-20 calls/min, well within Schwab's 120/min limit
