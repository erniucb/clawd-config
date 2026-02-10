import pandas as pd

def find_pivot_points(df, lookback=10):
    """
    Find local high and low points (pivot points).

    Args:
        df: DataFrame with 'high' and 'low' columns
        lookback: Number of bars before/after to check

    Returns:
        highs: List of dicts with 'index', 'price', 'time'
        lows: List of dicts with 'index', 'price', 'time'
    """
    highs = []
    lows = []

    for i in range(lookback, len(df) - lookback):
        # Check if current high is local maximum
        current_high = df['high'].iloc[i]
        window_high = df['high'].iloc[i-lookback:i+lookback+1].max()

        if current_high == window_high:
            highs.append({
                'index': i,
                'price': current_high,
                'time': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
            })

        # Check if current low is local minimum
        current_low = df['low'].iloc[i]
        window_low = df['low'].iloc[i-lookback:i+lookback+1].min()

        if current_low == window_low:
            lows.append({
                'index': i,
                'price': current_low,
                'time': df['timestamp'].iloc[i] if 'timestamp' in df.columns else None
            })

    return highs, lows

def detect_consolidation(df, index, min_bars=2, max_bars=3, max_range_percent=0.01):
    """
    Detect consolidation (sideways trading) patterns.

    Args:
        df: DataFrame with OHLC data
        index: Current bar index
        min_bars: Minimum bars for consolidation
        max_bars: Maximum bars for consolidation
        max_range_percent: Max price range as percentage of average price

    Returns:
        Dict with consolidation info or None
    """
    for length in range(min_bars, max_bars + 1):
        if index < length:
            continue

        window = df.iloc[index-length+1:index+1]
        price_range = window['high'].max() - window['low'].min()
        avg_price = (window['high'].max() + window['low'].min()) / 2
        range_percent = price_range / avg_price

        if range_percent <= max_range_percent:
            return {
                'start': index - length + 1,
                'end': index,
                'high': window['high'].max(),
                'low': window['low'].min(),
                'length': length
            }

    return None
