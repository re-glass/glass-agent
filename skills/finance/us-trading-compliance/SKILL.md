---
name: us-trading-compliance
title: US Trading Compliance Regulations
description: Key US brokerage and trading regulations
tags: [finance, trading, regulation, finra, sec, compliance, brokerage, day-trading, margin, retail-trader]
created: 2026-09-11
version: 1
---

# US Trading Compliance Regulations

## Overview

This skill tracks current US retail trading regulations as they evolve. Rules change — always verify with the latest FINRA/SEC guidance and your broker's implementation.

## Key Regulations (Current as of 2026-09-11)

### Pattern Day Trader (PDT) Rule — REPEALED

**Former rule (2001–June 2026):**
- 4+ day trades in 5 business days = "pattern day trader"
- Required $25,000 minimum equity in margin accounts
- Violation triggered 90-day trading restrictions

**Current status:** Repealed effective **June 4, 2026** (SEC approved FINRA proposal from January 2026).
- Replaced with **new intraday margin standards**
- Brokers have until **October 20, 2027** to fully implement
- Some brokers may still show PDT-era restrictions during transition

**Action:** Ask your broker specifically what their current intraday margin requirements are. Do not assume the old PDT limit applies — but do not assume it doesn't either until confirmed.

### Regulation T (Reg T) — ACTIVE
- Governs cash account settlement
- Stock trades settle **T+1** (changed from T+3 in 2024)
- **Free-riding prohibition:** Selling securities bought with unsettled funds triggers a 90-day cash-account freeze

### Cash Account vs Margin Account
- **Cash accounts:** No margin borrowing. Subject to free-riding rules and settlement timing. PDT rule never applied here.
- **Margin accounts:** Borrowing allowed. Formerly subject to PDT; now subject to new intraday margin standards.

## Broker-Specific Notes

### Charles Schwab
- Official API available (developer.schwab.com) with OAuth2
- Supports market data, account info, order execution
- Paper trading support available
- API is legitimate (not reverse-engineered like Robinhood)

### Robinhood
- No official public API
- Unofficial libraries exist but violate ToS and risk account termination
- Not recommended for automated trading

## Risk Parameters Commonly Used

| Parameter | Conservative | Moderate |
|-----------|-------------|----------|
| Risk per trade | 1% | 2% |
| Max daily drawdown | 3-5% | 5-7% |
| Max positions open | 1-2 | 3-5 |

## Pitfall: Outdated Regulatory Knowledge

**Scenario:** Agent advises user that PDT rule requires $25k to day trade. User corrects them — the rule was repealed in June 2026.

**Lesson:** Always verify current regulatory status before giving compliance advice. FINRA/SEC rules change. When in doubt, say "I believe X, but confirm with your broker" rather than stating it as fact.

**Verification sources:**
- FINRA Rule 4210 (Margin Requirements)
- SEC press releases on rule changes
- Broker's published margin agreement

## References

- `references/pdt-repeal.md` — Full timeline and sources for the PDT rule repeal (2001–2026)
- `references/` — Session-specific compliance detail; add new files here as regulations evolve (Reg T changes, SEC rulings, broker-specific policies, etc.)
