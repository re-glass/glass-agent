# Fetching 1-Minute Data with yfinance

## Problem

yfinance has strict limits on intraday data:
- `yf.download()` fails with "Only 8 days worth of 1m granularity data are allowed" for ranges >8 days
- Multi-index columns need flattening
- Timezone-aware timestamps complicate grouping

## Solution

**CRITICAL: Always use `Ticker.history()` for 1m data — never `yf.download()`.**

```python
import yfinance as yf

t = yf.Ticker('AAPL')
data = t.history(period='7d', interval='1m')

# Remove extra columns
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

# Remove timezone for easier grouping
data.index = data.index.tz_localize(None)
```

## Why This Works

- `Ticker.history()` doesn't have the same range limitation as `yf.download()`
- Returns at most ~8 days of 1m data (exchange limitation, not yfinance bug)
- For longer backtests, you'd need a different data source (Alpaca, Polygon, Interactive Brokers)

## VWAP Computation for Intraday

**IMPORTANT**: The `groupby().apply(lambda...).reset_index()` pattern fails with newer pandas versions. Use this safer pattern:

```python
def compute_vwap(df):
    df = df.copy()
    df['_date'] = df.index.date
    df['CumVol'] = df.groupby('_date')['Volume'].cumsum()
    df['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['CumVolPrice'] = (df['Volume'] * df['TypicalPrice']).groupby(df['_date']).cumsum()
    df['VWAP'] = df['CumVolPrice'] / df['CumVol']
    return df.drop(columns=['CumVol', 'CumVolPrice', 'TypicalPrice', '_date'])
```

## Bollinger Bands %B Range Note

BB_PctB is computed as `(Close - BB_Lower) / (BB_Upper - BB_Lower)`. It CAN and SHOULD go outside [0,1]:
- Values < 0: price below lower band (oversold / mean reversion long setup)
- Values > 1: price above upper band (overbought / mean reversion short setup)
- **Do not assert BB_PctB is in [0,1] in tests — that defeats the purpose of the indicator**

## Note on Data Quality

Free 1m data from Yahoo Finance:
- May have gaps or missing bars
- Not tick-accurate (aggregated from exchange data)
- Adjusted for splits/dividend (may differ from actual traded prices)
- For production scalping, consider paid data sources (Polygon, Alpaca, IBKR)
