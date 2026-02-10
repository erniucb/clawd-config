import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_price_path(years=1, start_price=100000, volatility=0.03, drift=0.0001):
    """
    Generate simulated 4-hour K-line data using geometric Brownian motion.

    Args:
        years: Number of years to simulate
        start_price: Starting price
        volatility: Daily volatility (BTC ~2-3%)
        drift: Daily drift rate

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    # 4-hour K-line count: 365 days * 6 bars/day = 2190 bars per year
    n_bars = int(years * 365 * 6)

    # Adjust parameters to 4-hour level
    # Use higher volatility for 4-hour bars to get ~0.005-0.05 range
    hourly_volatility = volatility / np.sqrt(6)  # Use sqrt scaling for time
    hourly_drift = drift / 6

    # Generate random walk with drift
    random_returns = np.random.normal(hourly_drift, hourly_volatility, n_bars)

    # Calculate price path using geometric Brownian motion
    log_prices = np.cumsum(random_returns)
    close_prices = start_price * np.exp(log_prices)

    # Generate OHLC from close prices
    opens = np.roll(close_prices, 1)
    opens[0] = start_price

    # Random intraday movement (±2% for more realistic volatility)
    up_noise = np.random.uniform(0, 0.02, n_bars)
    down_noise = np.random.uniform(0, 0.02, n_bars)

    # Ensure high >= max(open, close) and low <= min(open, close)
    highs = np.maximum(np.maximum(opens, close_prices) * (1 + up_noise), close_prices)
    lows = np.minimum(np.minimum(opens, close_prices) * (1 - down_noise), close_prices)

    # Generate timestamps (4-hour intervals starting from now)
    end_time = datetime.now()
    timestamps = [end_time - timedelta(hours=i*4) for i in reversed(range(n_bars))]

    # Generate random volume
    volumes = np.random.uniform(1000, 10000, n_bars)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': volumes
    })

    return df

def generate_multiple_paths(n_simulations=100, years=1):
    """
    Generate multiple price paths for Monte Carlo simulation.

    Args:
        n_simulations: Number of paths to generate
        years: Years per simulation

    Returns:
        List of DataFrames
    """
    paths = []
    for _ in range(n_simulations):
        df = generate_price_path(years=years)
        paths.append(df)
    return paths
