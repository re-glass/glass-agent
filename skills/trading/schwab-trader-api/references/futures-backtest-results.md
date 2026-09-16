# Futures Mean Reversion Backtest Results

## Session Results (7 days, 1-min bars, $1,000 capital)

| Ticker | Type | Trades | Win% | P&L | PF | W-Days | L-Days |
|--------|------|--------|------|-----|-----|--------|--------|
| SI=F | Futures | 114 | 49.1% | +$519.97 | 1.45 | 3 | 4 |
| QQQ | Stock/ETF | 36 | 61.1% | +$374.27 | 2.35 | 5 | 1 |
| CL=F | Futures | 212 | 42.0% | +$208.40 | 1.08 | 2 | 5 |
| SPY | Stock/ETF | 12 | 58.3% | +$109.93 | 2.11 | 1 | 0 |
| IWM | Stock/ETF | 47 | 44.7% | +$109.46 | 1.21 | 5 | 2 |
| YM=F | Futures | 49 | 38.8% | +$105.39 | 1.20 | 3 | 4 |
| ES=F | Futures | 33 | 45.5% | +$103.43 | 1.32 | 4 | 2 |
| NQ=F | Futures | 86 | 43.0% | +$49.61 | 1.06 | 2 | 3 |
| DIA | Stock/ETF | 11 | 18.2% | -$119.60 | 0.33 | 1 | 4 |
| GC=F | Futures | 53 | 32.1% | -$195.55 | 0.71 | 2 | 5 |

## Key Findings

### Futures Advantages
- **More trading hours** = more signal opportunities
- **SI=F (Silver)** was the top performer with 114 trades and +$520 P&L
- **CL=F (Crude Oil)** had the most trades (212) but lower per-trade profit

### Stock/ETF Performance
- **QQQ** had the highest profit factor (2.35) with 61.1% win rate
- **SPY** had 58.3% win rate but only 12 trades in 7 days
- **DIA** and **GC=F** were losing strategies

### Strategy Parameters (Optimized)
- SL Multiplier: 1.0x ATR
- TP Multiplier: 1.5x ATR
- RSI Oversold: 30
- RSI Overbought: 65
- Risk per Trade: 2%
- Max Daily Loss: 5%

## Recommendations

1. **For live testing**: Start with SI=F, CL=F, or ES=F (futures with most trades)
2. **For higher win rate**: QQQ or SPY (but fewer trading opportunities)
3. **Avoid**: DIA and GC=F (negative expectancy in backtest)
4. **Consider**: Running both stock and futures simultaneously for diversification

## Data Source
- yfinance: `yf.download(ticker, period='7d', interval='1m')`
- Note: yfinance limits 1m data to ~8 days per request
