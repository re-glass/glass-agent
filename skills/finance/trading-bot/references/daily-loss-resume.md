# Daily Loss Resume Option

## Problem
When the daily loss limit is hit, the bot stops trading for the day. Users may want to continue trading to recover losses.

## Solution
Add a `RESUME_ON_DAILY_LOSS` config option:

```python
class Config:
    MAX_DAILY_LOSS = 0.05  # 5% of account
    RESUME_ON_DAILY_LOSS = True  # Continue trading after hitting limit
```

## Implementation

```python
def _is_daily_loss_limit_hit(self) -> bool:
    """Check if daily loss limit is hit AND we should stop."""
    if self._check_daily_loss():
        return not self.config.RESUME_ON_DAILY_LOSS
    return False
```

In the run loop:

```python
if self._check_daily_loss():
    if self.config.RESUME_ON_DAILY_LOSS:
        log.warn(f"Daily loss limit hit (${self.daily_pnl:.2f}) — CONTINUING")
    else:
        log.warn(f"Daily loss limit hit (${self.daily_pnl:.2f}) — STOPPING")
        time.sleep(60)
        continue
```

## Behavior

| Setting | Behavior |
|---------|----------|
| `True` (default) | Logs warning, continues trading |
| `False` | Logs warning, stops trading for the day |

## Pitfall
When `RESUME_ON_DAILY_LOSS = True`, the bot will keep trading even after significant losses. Consider adding a **hard stop** at a higher loss threshold (e.g., 10%) that cannot be overridden.
