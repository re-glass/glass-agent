# yfinance Data Fetching

## Basic Usage
```python
import yfinance as yf

# Single chunk (max ~8 days for 1m data)
data = yf.download('AAPL', start='2025-01-01', end='2025-01-08', interval='1m')
```

## The 1-Minute Data Limit

**Problem:** yfinance limits 1-minute data to approximately 8 days per request.

**Error message:**
```
$AAPL: 1m data not available for startTime=... Only 8 days worth of 1m granularity data are allowed to be fetched per request.
```

## Workaround: Chunked Fetching

Fetch multiple chunks and combine:

```python
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def fetch_1m_chunked(ticker, chunks=6, chunk_days=8):
    """Fetch multiple chunks of 1m data."""
    all_data = []
    end_date = datetime.now()
    
    for i in range(chunks):
        chunk_start = end_date - timedelta(days=chunk_days * (i + 1))
        chunk_end = end_date - timedelta(days=chunk_days * i)
        
        data = yf.download(
            ticker,
            start=chunk_start.strftime('%Y-%m-%d'),
            end=chunk_end.strftime('%Y-%m-%d'),
            interval='1m',
            progress=False
        )
        if not data.empty:
            all_data.append(data)
    
    if not all_data:
        return pd.DataFrame()
    
    combined = pd.concat(all_data)
    # Remove duplicates and sort
    combined = combined[~combined.index.duplicated(keep='first')]
    combined.sort_index(inplace=True)
    return combined
```

## Important Notes

- **Rate limiting:** Don't make too many requests too quickly. Add `time.sleep(1)` between chunks if fetching many tickers.
- **Data gaps:** Chunk boundaries may have small gaps. Check for missing bars if precision matters.
- **Timezone:** yfinance returns UTC. Convert to market timezone (`US/Eastern`) for analysis.
- **Multi-level columns:** yfinance sometimes returns MultiIndex columns. Flatten with:
  ```python
  if isinstance(data.columns, pd.MultiIndex):
      data.columns = data.columns.get_level_values(0)
  ```

## Alternative: Ticker.history()

The `Ticker.history()` method sometimes works better than `yf.download()`:

```python
t = yf.Ticker('AAPL')
data = t.history(period='7d', interval='1m')
# Returns columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
# Filter to just OHLCV: data[['Open', 'High', 'Low', 'Close', 'Volume']]
```

## Estimated Data Available

| Period | Approximate Trading Days |
|--------|--------------------------|
| 7d | 5-7 days |
| 15d | 10-12 days |
| 30d | 20-22 days |
| 60d | 40-44 days |

1-minute data is only available for recent history. For older data, use 5-minute or daily bars.
