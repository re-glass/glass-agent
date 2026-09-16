# Scalping Bot — Unified Trading Bot

A professional-grade automated trading bot for stocks and futures via Schwab API.

## Quick Start

```bash
cd /home/reg/scalping_bot
source venv/bin/activate
python3 trading_bot.py
```

## Features

- **Markets:** FAANG stocks, Futures (YM, GC, ES, NQ, CL, SI)
- **Strategies:** Mean Reversion, Trend Following, Swing
- **Safety:** Graceful shutdown, position persistence, risk management
- **Optimization:** Automated parameter grid search

## Configuration

Edit `trading_bot.py`:

```python
# Markets
TICKERS = ['/YM', '/GC', '/ES', '/NQ', '/CL', '/SI']  # Futures
# TICKERS = ['AAPL', 'GOOGL', 'META', 'AMZN', 'NFLX']  # Stocks

# Strategy
STRATEGY = 'mean_reversion'  # or 'trend_following' or 'swing'

# Safety
PAPER_TRADING = True  # Set to False only after thorough testing
```

## Files

| File | Purpose |
|------|---------|
| `trading_bot.py` | Main bot (USE THIS) |
| `optimize.py` | Parameter optimization |
| `strategy_comparison.py` | Backtest strategies on futures + stocks |
| `futures_backtest.py` | Backtest mean reversion on futures |
| `enhanced_backtest.py` | Backtest on stocks with optimization |

## Disclaimer

This is experimental software. Past backtest results do not guarantee future performance. Always paper trade before risking real capital.
