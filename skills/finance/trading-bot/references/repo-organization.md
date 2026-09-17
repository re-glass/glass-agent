# Repository Organization

## Two-Repo Structure

Trading code and agent config must live in SEPARATE GitHub repos:

| Repo | Contents | URL |
|------|----------|-----|
| `TradingBot-code` | Trading bot code, backtests, optimization | `github.com/re-glass/TradingBot-code` |
| `glass-agent` | Hermes agent skills, memories, config | `github.com/re-glass/glass-agent` |

## Why Separate?

1. **Security** — Agent config may contain auth tokens, API keys. Trading repo is shared more freely.
2. **Clarity** — Each repo has a single purpose.
3. **Deployment** — Trading bot runs on a server. Agent runs locally.
4. **Collaboration** — Different contributors may have access to one but not the other.

## What Goes Where

### TradingBot-code
- `trading_bot.py` — Main bot
- `optimize.py` — Parameter optimization
- `strategy_comparison.py` — Backtest all strategies
- `futures_backtest.py` — Futures-specific backtest
- `enhanced_backtest.py` — Stock-specific backtest
- `FAANG_SCALPING_STRATEGY.md` — Strategy reference
- `requirements.txt` — Python dependencies

### glass-agent
- `skills/` — All Hermes agent skills
- `memories/` — Agent memory files
- `SOUL.md` — Agent personality
- `config.yaml` — Hermes configuration

## Cross-Repo .gitignore

Each repo's `.gitignore` should exclude the other repo's files:

**glass-agent/.gitignore:**
```
# Trading bot files (separate repo)
trading_bot.py
live_bot.py
live_bot_futures.py
optimize.py
futures_backtest.py
strategy_comparison.py
enhanced_backtest.py
positions.json
tokens.json
optimization_results.json
```

**TradingBot-code/.gitignore:**
```
# Agent files (separate repo)
skills/
memories/
SOUL.md
config.yaml
```

## Remote Configuration

```bash
# In TradingBot-code
git remote add trading-code https://github.com/re-glass/TradingBot-code.git
git push -u trading-code master

# In glass-agent
git remote add glass-agent https://github.com/re-glass/glass-agent.git
git push -u glass-agent master
```

## Pitfall: Accidental Mix-up

If you find trading code in the agent repo or vice versa:
1. Remove the misplaced files
2. Update .gitignore to exclude them
3. Commit and push to correct repo
