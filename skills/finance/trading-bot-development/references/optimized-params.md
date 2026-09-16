# Optimized Strategy Parameters

## Futures Mean Reversion (14-day backtest, 6 tickers, 1296 combinations tested)

### Best Parameters (Profit Factor)
| Parameter | Value |
|-----------|-------|
| ATR SL Mult | 1.0 |
| ATR TP Mult | 2.0 |
| RSI Oversold | 25 |
| RSI Overbought | 75 |
| VWAP Deviation | 0.3% |
| BB Std Dev | 1.5 |

**Results**: PF=1.39, P&L=$2,199, MaxDD=$406, Win%=40.4%, Trades=495

### Best Parameters (Total P&L)
| Parameter | Value |
|-----------|-------|
| ATR SL Mult | 0.8 |
| ATR TP Mult | 2.0 |
| RSI Oversold | 35 |
| RSI Overbought | 65 |
| VWAP Deviation | 0.3% |
| BB Std Dev | 1.5 |

**Results**: PF=1.35, P&L=$3,080, MaxDD=$452, Win%=34.9%, Trades=708

### Key Insights
1. **Wider TP (2.0x ATR)** works better than 1.5x for futures — futures trend more than stocks
2. **Tighter BB (1.5 std)** catches more setups in volatile futures markets
3. **RSI 25/75** (vs 30/70 for stocks) gives more selective, higher-quality entries
4. **Binary trade distribution** (trades mostly hit either SL or TP) indicates systematic execution
5. **Live paper trading confirmed**: Gold short +$7.82, Crude Oil long +$8.97 in first hour

### Per-Ticker Performance (Best PF config)
| Ticker | Contribution |
|--------|-------------|
| YM=F (Dow) | Strong |
| GC=F (Gold) | Strong across all strategies |
| CL=F (Crude) | Good |
| SI=F (Silver) | Best mean reversion performer |
| ES=F (S&P) | Moderate |
| NQ=F (Nasdaq) | Weakest — consider dropping |

### Recommendations
- Drop NQ=F if it continues underperforming
- Gold (GC=F) is the most robust across all strategies
- Consider ES+F (S&P + Nasdaq) as a correlated pair — don't hold simultaneously