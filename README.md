# TradingBot-code

FAANG Mean Reversion Scalping Bot with Schwab API

## Structure

- `live_bot.py` — Main trading bot (verified, 6/6 tests pass)
- `enhanced_backtest.py` — Full optimization backtest (48 days, 81 parameter combos)
- `FAANG_SCALPING_STRATEGY.md` — Complete strategy reference document
- `requirements.txt` — Python dependencies

## Status

- Strategy: Mean Reversion only (trend following removed — was losing money)
- Entry: price >0.3% from VWAP + RSI <30 or >65 + BB %B <0.1 or >0.9
- Exit: SL=1.0x ATR, TP=1.5x ATR
- Risk: 2% per trade, 5% daily kill switch, max 2 positions
- Backtest: 48 days, 1015 trades, +$1695 P&L, Profit Factor=1.15
- **Pending:** Schwab API credentials at developer.schwab.com

## Quick Start

```bash
pip install -r requirements.txt
# Add your Schwab App Key/Secret to live_bot.py
python live_bot.py
```

## Tickers

AAPL, GOOGL, META, AMZN, NFLX

## Disclaimer

Strategy is experimental. Past backtest results do not guarantee future performance. Always paper trade before risking real capital.
