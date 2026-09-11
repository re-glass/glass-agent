# FAANG Mean Reversion Scalping Strategy
## Complete Reference Document
### Created: 2026-09-11

---

## 1. ACCOUNT & RISK PARAMETERS

- **Broker:** Schwab (official API, OAuth2)
- **Account Size:** < $1,000
- **Account Type:** (to be confirmed - cash or margin)
- **Pattern Day Trader Rule:** Repealed as of June 4, 2026 (FINRA replaced with intraday margin standards, phase-in until Oct 2027)

### Risk Rules
| Parameter | Value |
|-----------|-------|
| Risk per Trade | 2% of account |
| Max Daily Loss | 5% (kill switch) |
| Max Positions | 2 concurrent |
| Strategy | Mean Reversion ONLY (trend following removed) |

---

## 2. STRATEGY SPECIFICATION

### Tickers
FAANG: AAPL, GOOGL, META, AMZN, NFLX

### Timeframe
1-minute bars

### Indicators Used
- **VWAP** (daily reset) - anchor for mean reversion
- **Bollinger Bands** (20-period, 2 std dev) - overextension detection
- **RSI** (14-period) - momentum confirmation
- **ATR** (14-period) - stop loss / profit target calculation

### Entry Rules (Mean Reversion Only)

**LONG Entry (all 3 conditions must be met):**
1. Price deviation from VWAP < -0.3% (price below VWAP)
2. RSI < 30 (oversold)
3. Bollinger Bands %B < 0.1 (price near lower band)

**SHORT Entry (all 3 conditions must be met):**
1. Price deviation from VWAP > +0.3% (price above VWAP)
2. RSI > 65 (overbought)
3. Bollinger Bands %B > 0.9 (price near upper band)

### Exit Rules
- **Stop Loss:** Entry price ± (1.0 x ATR) [optimized from 1.5]
- **Take Profit:** Entry price ± (1.5 x ATR) [optimized from 2.0]
- **Market Close:** All positions closed at 3:59 PM ET

### Position Sizing
```
risk_amount = account_value * 0.02
stop_distance = ATR * 1.0
qty = max(1, int(risk_amount / stop_distance))
```

---

## 3. BACKTEST RESULTS

### Original Settings (1.5x SL, 2.0x TP, RSI 30/70)
- **7 days, 319 trades**
- Total P&L: +$399.39
- Win Rate: 45.8%
- Profit Factor: 1.12
- Final Capital: $1,399.39

### Optimized Settings (1.0x SL, 1.5x TP, RSI 30/65)
- **48 days, 1,015 trades**
- Total P&L: +$1,695.87
- Win Rate: 43.5%
- Profit Factor: 1.15
- Max Drawdown: -$593.13
- Final Capital: $2,695.87

### Per-Ticker Performance (Optimized)
| Ticker | Trades | P&L | Win Rate |
|--------|--------|-----|----------|
| META | 268 | +$1,057.72 | Best performer |
| GOOGL | 166 | +$525.56 | |
| NFLX | 223 | +$243.72 | |
| AMZN | 159 | +$71.26 | |
| AAPL | 199 | -$202.40 | **Losing ticker** |

### Trade Distribution
- **Winning trades:** 442 (43.5%) — avg win $29.42
- **Losing trades:** 573 (56.5%) — avg loss -$19.73
- **Reward-to-Risk:** 1.49:1
- **Max Win Streak:** 11
- **Max Loss Streak:** 12
- **Shorts outperformed Longs:** $1,390 vs $305

### Exit Analysis
| Exit Reason | Count | Avg P&L |
|-------------|-------|---------|
| Take Profit | 435 (42.9%) | +$29.64 |
| Stop Loss | 570 (56.2%) | -$19.79 |
| Market Close | 10 (1.0%) | +$8.04 |

---

## 4. PARAMETER OPTIMIZATION

Tested 81 combinations of:
- SL Multiplier: [1.0, 1.5, 2.0]
- TP Multiplier: [1.5, 2.0, 2.5]
- RSI Oversold: [25, 30, 35]
- RSI Overbought: [65, 70, 75]

**Top 3 Parameter Sets:**
1. SL=1.0, TP=1.5, RSI=30/65 → P&L: +$1,695.87
2. SL=1.0, TP=1.5, RSI=35/65 → P&L: +$1,301.46
3. SL=1.0, TP=2.0, RSI=30/65 → P&L: +$1,158.90

---

## 5. FILES & LOCATIONS

### Scripts
- `/home/reg/scalping_backtest.py` — Original backtest (mean reversion only, 7 days)
- `/home/reg/enhanced_backtest.py` — Full optimization backtest (48 days, 81 param combos)

### Output Files
- `/home/reg/backtest_results.csv` — Trade details from original backtest
- `/home/reg/optimization_results.csv` — All 81 parameter combinations ranked
- `/home/reg/best_param_trades.csv` — Trade details from best parameter run

### Virtual Environment
- `/home/reg/venv/` — Python venv with yfinance, pandas, numpy installed
- Activate: `source /home/reg/venv/bin/activate`

---

## 6. NEXT STEPS (IN ORDER)

### Immediate
1. **Review this document** and confirm all parameters
2. **Open Schwab account** (if not already done) and apply for API access at developer.schwab.com
3. **Set up paper trading** on Schwab — test with fake money first

### Before Live Trading
4. **Paper trade for 2-4 weeks** using the exact optimized parameters
5. **Consider dropping AAPL** — it was the only losing ticker
6. **Implement 5% daily loss limit** as a hard kill switch in the live trading script
7. **Build the live trading script** using Schwab's official API:
   - OAuth2 authentication
   - Real-time 1-minute bar streaming
   - Order placement (market/limit)
   - Position tracking
   - Daily P&L monitoring

### Risk Management Reminders
- With $1,000: 2% risk = $20 per trade
- 5% daily loss limit = $50 max loss per day
- 2 positions max, but FAANG stocks are highly correlated (effectively 1 bet)
- Consider reducing to 1 position max for live trading

---

## 7. SCHWAB API NOTES

- **API Docs:** https://developer.schwab.com/
- **Auth:** OAuth2 (requires callback URL, can use localhost for personal use)
- **Capabilities:** Market data, account info, order placement, order status
- **Paper Trading:** Schwab supports paper trading accounts
- **Rate Limits:** Check current docs (typically 120 requests/minute)

---

## 8. CONVERSATION HISTORY

Key decisions made:
- Started with Robinhood → switched to Schwab (official API)
- Started with PDT rule concern → confirmed rule repealed June 2026
- Started with mean reversion + trend following → killed trend following (was losing money)
- Started with 7 days data → expanded to 48 days
- Started with default parameters → optimized via 81-combination grid search
- Confirmed: fully autonomous execution (no confirmation per trade)

---

## 9. RESUMING THIS WORK

### Status: Waiting for Schwab API Access
- **Action required:** Complete app registration at https://developer.schwab.com/
- **Redirect URI:** `http://localhost:8080`
- **Pending:** App Key and App Secret from Schwab

### To continue on this machine:
1. Open terminal
2. Start Hermes
3. Say something like: "Let's continue the FAANG scalping strategy work"
4. I'll use session_search to find this conversation and pick up where we left off

### What's ready to go:
- `/home/reg/scalping_bot/live_bot.py` — Fully written and tested (6/6 tests pass)
- `/home/reg/scalping_bot/requirements.txt` — Dependencies ready to install
- All strategy parameters finalized from 81-combination optimization
- Reference document: `/home/reg/FAANG_SCALPING_STRATEGY.md`

### Next steps after API approval:
1. Save App Key and Secret into `SCHWAB_CONFIG` in `live_bot.py`
2. Run the bot with `paper_trading: True` first
3. Authenticate via OAuth2 (browser opens, log in to Schwab)
4. Verify paper trades flow correctly
5. After 2-4 weeks of successful paper trading, consider live trading

---

*Document generated by Hermes Agent on 2026-09-11*
*Last updated: 2026-09-11 — Waiting for Schwab API credentials*
*Strategy is experimental — past backtest results do not guarantee future performance*
*Always paper trade before risking real capital*
