import pandas as pd
import numpy as np
from backtest_system.data_generator import generate_price_path

def test_generate_price_path_shape():
    """Test that generated data has correct shape"""
    df = generate_price_path(years=1)
    assert len(df) > 2000  # Approximately 2190 bars for 1 year
    assert 'timestamp' in df.columns
    assert 'open' in df.columns
    assert 'high' in df.columns
    assert 'low' in df.columns
    assert 'close' in df.columns
    assert 'volume' in df.columns

def test_generate_price_path_ohlc_relationship():
    """Test that OHLC values are correct (high >= open, close >= low, etc)"""
    df = generate_price_path(years=0.1)  # Short test
    for _, row in df.iterrows():
        assert row['high'] >= row['open']
        assert row['high'] >= row['close']
        assert row['low'] <= row['open']
        assert row['low'] <= row['close']
        assert row['high'] >= row['low']

def test_generate_price_path_volatility():
    """Test that price has reasonable volatility"""
    df = generate_price_path(years=1)
    returns = df['close'].pct_change().dropna()
    volatility = returns.std()
    # Should be around 2% daily, adjusted for 4-hour bars
    assert 0.005 < volatility < 0.05
