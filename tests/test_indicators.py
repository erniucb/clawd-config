import pandas as pd
from backtest_system.indicators import find_pivot_points

def test_find_pivot_points_basic():
    """Test basic pivot point detection"""
    # Create simple price data with clear high and low
    data = {
        'high': [100, 105, 110, 115, 110, 105, 100],
        'low': [95, 100, 105, 110, 105, 100, 95]
    }
    df = pd.DataFrame(data)

    highs, lows = find_pivot_points(df, lookback=1)

    # Index 3 (value 115) should be a high point
    assert len(highs) > 0
    assert highs[0]['price'] == 115
    assert highs[0]['index'] == 3

def test_find_pivot_points_multiple():
    """Test detection of multiple pivot points"""
    # Create data with two peaks
    data = {
        'high': [100, 110, 100, 110, 100],
        'low': [90, 100, 90, 100, 90]
    }
    df = pd.DataFrame(data)

    highs, lows = find_pivot_points(df, lookback=1)

    # Should find 2 high points
    assert len(highs) == 2
    assert highs[0]['price'] == 110
    assert highs[1]['price'] == 110
