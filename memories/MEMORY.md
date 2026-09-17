Session built FAANG mean reversion scalping bot → expanded to futures via Schwab API. Key findings: futures quotes return 404 (use price history), extended.lastPrice is stale (use quote.lastPrice), futures use /YM format not YM=F, account hashValue not accountNumber. Multi-strategy backtest: Mean Reversion on YM=F best (PF=2.68), Trend Following on GC=F (PF=1.41), Swing on GC=F (PF=1.23). Updated schwab-trader-api skill with all findings.
§
Schwab day trader (<$1000), FAANG + futures (/YM /GC /ES /NQ /CL /SI), 1-min mean-reversion scalping. Risk: 2%/5%/max 2 pos. Fully autonomous, paper first. Two repos: TradingBot-code (bot), glass-agent (agent files). Schwab API: MarketData + AccountsAndTrading scopes. PDT repealed June 2026; intraday margin standards phase-in to Oct 2027.
§
Schwab API pitfalls learned: 3 base URLs (OAuth /v1, Trader /trader/v1, Market Data /marketdata/v1). Account endpoint needs hashValue not accountNumber. Futures /quotes 404 — use /pricehistory for all prices. Stock live price: quote.lastPrice (extended.lastPrice stale fallback). Futures symbols: /YM format (not YM=F). Auth code parsing: strip &session= suffix.
§
New project: GlassTB — integrated trading bot + GUI app at /home/reg/GlassTB/. Flask + pywebview, bot runs in background thread, Start/Stop buttons on dashboard, trade log. Committed bad6923 locally, needs PAT to push to GitHub.
§
GitHub PAT for pushing to new repos must be provided by user (not stored/redacted in git config). Setting remote on new repos requires PAT.
§
GlassTB — integrated trading bot + native GUI (Flask + pywebview). Created new GitHub repo. Key fixes: Schwab API rejects `fields` param (returns 400); tick() must always reschedule; stop_bot() must flip button immediately; charts need log scale for bars + absolute positioning for candles; no duplicate UI sections; no 7c column.
§
GitHub repo for GlassTB: https://github.com/re-glass/GlassTB (was TradingBot-code). PAT stored in git config (redacted). User prefers: no duplicate UI sections, no 7c column, no chart column (Symbol + Price only), bot button flips immediately on stop.