# yfinance Data Fetching Guide

## Overview

yfinance has specific limitations for intraday data that require workarounds.

## 1-Minute Data Limitations

- **Maximum range**: ~8 days per request
- **`yf.download()` fails** for ranges > 8 days with cryptic errors
- **`Ticker.history()` works** for the same ranges

## Correct Approach

```python
import yfinance as yf

# For recent 1m data (last 7 days)
t = yf.Ticker('AAPL')
data = t.history(period='7d', interval='1m')
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
```

## Fetching Extended History

To get more than 8 days of 1m data:

```python
def fetch_extended_1m(ticker, chunks=6, chunk_days=8):
    """Fetch multiple 8-day chunks and combine."""
    all_data = []
    end_date = datetime.now()
    
    for i in range(chunks):
        chunk_start = end_date - timedelta(days=chunk_days * (i + 1))
        chunk_end = end_date - timedelta(days=chunk_days * i)
        
        t = yf.Ticker(ticker)
        data = t.history(
            start=chunk_start.strftime('%Y-%m-%d'),
            end=chunk_end.strftime('%Y-%m-%d'),
            interval='1m'
        )
        if not data.empty:
            all_data.append(data[['Open', 'High', 'Low', 'Close', 'Volume']])
    
    combined = pd.concat(all_data)
    combined = combined[~combined.index.duplicated(keep='first')]
    combined.sort_index(inplace=True)
    return combined
```

## Timezone Handling

yfinance returns timestamps in the exchange timezone (e.g., `US/Eastern`).

```python
# Convert to timezone-naive for easier grouping
df.index = df.index.tz_localize(None)

# Or convert to UTC
df.index = df.index.tz_convert('UTC')
```

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "1m data not available for startTime=..." | Date range too old or too wide | Use `Ticker.history()` with `period` parameter |
| "Only 8 days worth of 1m granularity data..." | Range exceeds limit | Fetch in chunks |
| "The requested range must be within the last 30 days" | Date is in the past beyond 30 days | Use more recent date range |
| Multi-level columns | `yf.download()` returns MultiIndex | Flatten: `data.columns = data.columns.get_level_values(0)` |
