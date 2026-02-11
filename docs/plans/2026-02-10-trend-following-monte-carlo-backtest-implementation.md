# Trend Following Monte Carlo Backtest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Monte Carlo backtesting system for a trend-following trading strategy with 100 simulations and comprehensive statistical analysis.

**Architecture:** Modular Python system with 5 components (data generator, strategy engine, Monte Carlo simulator, analytics, reporter) that runs simulations, executes the three-phase entry strategy with dynamic stop-loss management, and generates statistical reports.

**Tech Stack:** Python 3.10+, pandas, numpy, matplotlib (for charts)

---

## Task 1: Create Project Structure

**Files:**
- Create: `backtest_system/__init__.py`
- Create: `backtest_system/data_generator.py`
- Create: `backtest_system/strategy_engine.py`
- Create: `backtest_system/monte_carlo.py`
- Create: `backtest_system/analytics.py`
- Create: `backtest_system/reporter.py`
- Create: `backtest_system/config.json`
- Create: `tests/__init__.py`
- Create: `tests/test_data_generator.py`

**Step 1: Create project directory structure**

```bash
mkdir -p backtest_system tests
```

**Step 2: Create __init__ files**

```bash
touch backtest_system/__init__.py tests/__init__.py
```

**Step 3: Create empty module files**

```bash
touch backtest_system/data_generator.py backtest_system/strategy_engine.py
touch backtest_system/monte_carlo.py backtest_system/analytics.py
touch backtest_system/reporter.py
touch tests/test_data_generator.py
```

**Step 4: Verify structure**

```bash
tree backtest_system tests
```

Expected:
```
backtest_system/
├── __init__.py
├── data_generator.py
├── strategy_engine.py
├── monte_carlo.py
├── analytics.py
├── reporter.py
└── config.json
tests/
├── __init__.py
└── test_data_generator.py
```

**Step 5: Commit**

```bash
git add backtest_system tests
git commit -m "chore: create project structure for backtest system"
```

---

## Task 2: Implement Data Generator

**Files:**
- Modify: `backtest_system/data_generator.py`

**Step 1: Write the failing test**

```python
# tests/test_data_generator.py
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
```

**Step 2: Run tests to verify they fail**

```bash
cd /root/clawd && python -m pytest tests/test_data_generator.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'backtest_system'"

**Step 3: Write minimal implementation**

```python
# backtest_system/data_generator.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_price_path(years=1, start_price=100000, volatility=0.02, drift=0.0001):
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
    hourly_volatility = volatility / 6
    hourly_drift = drift / 6

    # Generate random walk with drift
    random_returns = np.random.normal(hourly_drift, hourly_volatility, n_bars)

    # Calculate price path using geometric Brownian motion
    log_prices = np.cumsum(random_returns)
    close_prices = start_price * np.exp(log_prices)

    # Generate OHLC from close prices
    opens = np.roll(close_prices, 1)
    opens[0] = start_price

    # Random intraday movement (±1%)
    noise = np.random.uniform(-0.01, 0.01, n_bars)
    highs = close_prices * (1 + np.abs(noise))
    lows = close_prices * (1 - np.abs(noise))

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
```

**Step 4: Run tests to verify they pass**

```bash
cd /root/clawd && python -m pytest tests/test_data_generator.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backtest_system/data_generator.py tests/test_data_generator.py
git commit -m "feat: implement data generator with geometric Brownian motion"
```

---

## Task 3: Implement Pivot Point Detection

**Files:**
- Create: `backtest_system/indicators.py`
- Create: `tests/test_indicators.py`

**Step 1: Write the failing test**

```python
# tests/test_indicators.py
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
```

**Step 2: Run test to verify it fails**

```bash
cd /root/clawd && python -m pytest tests/test_indicators.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backtest_system/indicators.py
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
```

**Step 4: Run tests to verify they pass**

```bash
cd /root/clawd && python -m pytest tests/test_indicators.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backtest_system/indicators.py tests/test_indicators.py
git commit -m "feat: implement pivot point and consolidation detection"
```

---

## Task 4: Implement Trading Strategy Engine

**Files:**
- Modify: `backtest_system/strategy_engine.py`
- Create: `tests/test_strategy_engine.py`

**Step 1: Write the failing test**

```python
# tests/test_strategy_engine.py
from backtest_system.strategy_engine import TrendFollowingStrategy, Position, Portfolio

def test_position_creation():
    """Test position creation with correct risk calculation"""
    pos = Position(
        entry_price=100,
        stop_loss=95,
        initial_capital=10000,
        risk_percent=0.02
    )

    # Position size = (10000 * 0.02) / (100 - 95) = 40 units
    expected_size = (10000 * 0.02) / (100 - 95)
    assert abs(pos.size - expected_size) < 0.001

    # Risk amount should be 200 (2% of 10000)
    assert abs(pos.risk_amount - 200) < 0.01

def test_position_state_tracking():
    """Test position state (risk vs profit)"""
    pos = Position(entry_price=100, stop_loss=95, initial_capital=10000, risk_percent=0.02)

    # Initial state: stop_loss < entry_price -> risk state
    assert pos.is_risky() == True
    assert pos.is_safe() == False

    # Update stop loss to entry price -> safe state
    pos.update_stop_loss(100)
    assert pos.is_risky() == False
    assert pos.is_safe() == True

def test_portfolio_risk_check():
    """Test portfolio risk limit enforcement"""
    portfolio = Portfolio(initial_capital=10000, max_risk_positions=3)

    # Add 3 risky positions
    for i in range(3):
        pos = Position(entry_price=100+i, stop_loss=95+i, initial_capital=10000, risk_percent=0.02)
        portfolio.add_position(pos)

    # Should have exactly 3 risky positions
    assert portfolio.get_risky_count() == 3

    # Should not allow 4th risky position
    pos4 = Position(entry_price=105, stop_loss=100, initial_capital=10000, risk_percent=0.02)
    assert portfolio.can_open_position(pos4) == False

    # Add a safe position
    safe_pos = Position(entry_price=100, stop_loss=95, initial_capital=10000, risk_percent=0.02)
    safe_pos.update_stop_loss(100)  # Make it safe
    portfolio.add_position(safe_pos)

    # Should still have only 3 risky positions
    assert portfolio.get_risky_count() == 3

    # Now can open new risky position (safe position doesn't count)
    pos5 = Position(entry_price=110, stop_loss=105, initial_capital=10000, risk_percent=0.02)
    assert portfolio.can_open_position(pos5) == True
```

**Step 2: Run tests to verify they fail**

```bash
cd /root/clawd && python -m pytest tests/test_strategy_engine.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backtest_system/strategy_engine.py
import pandas as pd
from typing import List, Optional
from backtest_system.indicators import find_pivot_points, detect_consolidation

class Position:
    """Single trading position with stop-loss management"""

    def __init__(self, entry_price: float, stop_loss: float,
                 initial_capital: float, risk_percent: float):
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.initial_stop_loss = stop_loss
        self.initial_capital = initial_capital
        self.risk_percent = risk_percent

        # Calculate position size based on risk
        self.risk_distance = entry_price - stop_loss
        self.size = (initial_capital * risk_percent) / self.risk_distance
        self.risk_amount = self.size * self.risk_distance

        # Track highest stop loss reached (for safe state)
        self.highest_stop_loss = stop_loss

    def is_risky(self) -> bool:
        """Check if position is still at risk (stop loss < entry)"""
        return self.stop_loss < self.entry_price

    def is_safe(self) -> bool:
        """Check if position is safe (stop loss >= entry)"""
        return self.stop_loss >= self.entry_price

    def update_stop_loss(self, new_stop_loss: float):
        """Update stop loss (only upward moves allowed)"""
        if new_stop_loss > self.stop_loss:
            self.stop_loss = new_stop_loss
            if new_stop_loss > self.highest_stop_loss:
                self.highest_stop_loss = new_stop_loss

    def check_stop_loss(self, current_price: float) -> bool:
        """Check if stop loss is triggered"""
        return current_price <= self.stop_loss

    def close(self, exit_price: float) -> float:
        """Calculate profit/loss"""
        return (exit_price - self.entry_price) * self.size


class Portfolio:
    """Manage multiple positions with risk limits"""

    def __init__(self, initial_capital: float, max_risk_positions: int = 3):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_positions = max_risk_positions
        self.positions: List[Position] = []
        self.trades = []

    def add_position(self, position: Position):
        """Add a position to portfolio"""
        self.positions.append(position)

    def remove_position(self, position: Position, exit_price: float):
        """Remove position and record trade"""
        pnl = position.close(exit_price)
        self.current_capital += pnl
        self.positions.remove(position)

        self.trades.append({
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'size': position.size,
            'pnl': pnl,
            'exit_type': 'stop_loss' if exit_price <= position.stop_loss else 'take_profit'
        })

    def get_risky_count(self) -> int:
        """Count positions that are still at risk"""
        return sum(1 for pos in self.positions if pos.is_risky())

    def can_open_position(self, position: Position) -> bool:
        """Check if new position can be opened (risk limit not exceeded)"""
        if not position.is_risky():
            return True  # Safe positions don't count toward limit
        return self.get_risky_count() < self.max_risk_positions


class TrendFollowingStrategy:
    """Three-phase trend following strategy implementation"""

    def __init__(self, config: dict):
        self.config = config
        self.lookback_bars = config.get('lookback_bars', 60)
        self.pivot_lookback = config.get('pivot_lookback', 10)

        # Entry phase tracking
        self.phase = 0  # 0: wait breakout, 1: wait pullback, 2: wait re-breakout
        self.breakout_high = None  # Breakout bar's high
        self.pivot_high = None  # High before breakout
        self.pullback_low = None  # Lowest price during pullback

    def reset_state(self):
        """Reset entry state after failed entry"""
        self.phase = 0
        self.breakout_high = None
        self.pivot_high = None
        self.pullback_low = None

    def analyze(self, df: pd.DataFrame, current_index: int) -> dict:
        """
        Analyze current bar and generate signal.

        Returns:
            Dict with 'action', 'entry_price', 'stop_loss', etc.
        """
        # Get recent pivot points
        highs, lows = find_pivot_points(df.iloc[:current_index+1], lookback=self.pivot_lookback)

        if not highs:
            return {'action': 'hold'}

        # Get most recent high
        recent_high = highs[-1]

        if self.phase == 0:
            return self.check_breakout(df, current_index, recent_high)
        elif self.phase == 1:
            return self.check_pullback(df, current_index)
        elif self.phase == 2:
            return self.check_re_breakout(df, current_index)

        return {'action': 'hold'}

    def check_breakout(self, df: pd.DataFrame, current_index: int, recent_high: dict) -> dict:
        """Check for initial breakout above pivot high"""
        current_bar = df.iloc[current_index]

        # Check if current bar closes above pivot high
        if current_bar['close'] > recent_high['price']:
            self.phase = 1
            self.pivot_high = recent_high['price']
            self.breakout_high = current_bar['high']

            return {'action': 'breakout_detected', 'price': current_bar['close']}

        return {'action': 'hold'}

    def check_pullback(self, df: pd.DataFrame, current_index: int) -> dict:
        """Check for pullback that doesn't break pivot high"""
        current_bar = df.iloc[current_index]

        # Track lowest price during pullback
        if self.pullback_low is None or current_bar['low'] < self.pullback_low:
            self.pullback_low = current_bar['low']

        # If pullback goes below pivot high, reset
        if self.pullback_low < self.pivot_high:
            self.reset_state()
            return {'action': 'hold'}

        # Detect consolidation (end of pullback)
        consolidation = detect_consolidation(
            df.iloc[:current_index+1],
            current_index,
            min_bars=2,
            max_bars=3
        )

        if consolidation:
            self.phase = 2
            return {'action': 'pullback_confirmed', 'consolidation': consolidation}

        return {'action': 'hold'}

    def check_re_breakout(self, df: pd.DataFrame, current_index: int) -> dict:
        """Check for re-breakout above initial breakout high"""
        current_bar = df.iloc[current_index]

        # Check if price exceeds initial breakout high
        if current_bar['close'] > self.breakout_high:
            entry_price = current_bar['close']
            stop_loss = self.pullback_low

            signal = {
                'action': 'buy',
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'breakout_high': self.breakout_high,
                'pullback_low': self.pullback_low
            }

            self.reset_state()
            return signal

        return {'action': 'hold'}

    def update_positions(self, df: pd.DataFrame, portfolio: Portfolio, current_index: int):
        """
        Update all positions, check for stop losses, manage stop loss adjustments.
        """
        current_bar = df.iloc[current_index]
        current_price = current_bar['close']

        positions_to_close = []

        for pos in portfolio.positions:
            # Check stop loss trigger
            if pos.check_stop_loss(current_price):
                positions_to_close.append(pos)
                continue

            # Only update stop loss if position is already safe or could become safe
            if pos.is_safe() or current_price >= pos.entry_price:
                # Check for consolidation to move stop loss
                consolidation = detect_consolidation(
                    df.iloc[:current_index+1],
                    current_index,
                    min_bars=2,
                    max_bars=3
                )

                if consolidation:
                    # Move stop loss to consolidation low (or entry price for first consolidation)
                    if pos.is_risky():
                        # First consolidation: move to entry price
                        new_stop = pos.entry_price
                    else:
                        # Subsequent consolidation: move to previous consolidation
                        new_stop = consolidation['low']

                    if new_stop > pos.stop_loss:
                        pos.update_stop_loss(new_stop)

        # Close positions that hit stop loss
        for pos in positions_to_close:
            portfolio.remove_position(pos, current_price)


def run_backtest(df: pd.DataFrame, config: dict) -> dict:
    """
    Run complete backtest on a single price path.

    Returns:
        Dict with statistics: return, max_drawdown, trades, etc.
    """
    initial_capital = config.get('initial_capital', 10000)
    portfolio = Portfolio(initial_capital, max_risk_positions=config.get('max_risk_positions', 3))
    strategy = TrendFollowingStrategy(config)

    # Process each bar
    for i in range(config.get('lookback_bars', 60), len(df)):
        # Check for entry signals
        signal = strategy.analyze(df, i)

        if signal['action'] == 'buy':
            # Create position
            position = Position(
                entry_price=signal['entry_price'],
                stop_loss=signal['stop_loss'],
                initial_capital=portfolio.current_capital,
                risk_percent=config.get('risk_percent', 0.02)
            )

            # Check if we can open this position
            if portfolio.can_open_position(position):
                portfolio.add_position(position)

        # Update existing positions
        strategy.update_positions(df, portfolio, i)

    # Close all remaining positions at final price
    final_price = df['close'].iloc[-1]
    for pos in portfolio.positions.copy():
        portfolio.remove_position(pos, final_price)

    # Calculate statistics
    total_return = (portfolio.current_capital - initial_capital) / initial_capital

    # Calculate max drawdown
    equity_curve = [initial_capital]
    for trade in portfolio.trades:
        equity_curve.append(equity_curve[-1] + trade['pnl'])
    equity_curve.append(portfolio.current_capital)

    max_equity = max(equity_curve)
    max_drawdown = (max_equity - min(equity_curve)) / max_equity

    # Calculate win rate and average PnL
    if portfolio.trades:
        winning_trades = [t for t in portfolio.trades if t['pnl'] > 0]
        losing_trades = [t for t in portfolio.trades if t['pnl'] <= 0]

        win_rate = len(winning_trades) / len(portfolio.trades)
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0

    return {
        'initial_capital': initial_capital,
        'final_capital': portfolio.current_capital,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'total_trades': len(portfolio.trades),
        'winning_trades': len(portfolio.trades) - win_rate * len(portfolio.trades),
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'trades': portfolio.trades,
        'equity_curve': equity_curve
    }
```

**Step 4: Run tests to verify they pass**

```bash
cd /root/clawd && python -m pytest tests/test_strategy_engine.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backtest_system/strategy_engine.py tests/test_strategy_engine.py
git commit -m "feat: implement trend following strategy with risk management"
```

---

## Task 5: Implement Monte Carlo Simulator

**Files:**
- Modify: `backtest_system/monte_carlo.py`
- Create: `tests/test_monte_carlo.py`

**Step 1: Write the failing test**

```python
# tests/test_monte_carlo.py
from backtest_system.monte_carlo import run_monte_carlo

def test_run_monte_carlo_returns_results():
    """Test that Monte Carlo simulation returns correct number of results"""
    config = {
        'simulations': 5,  # Small number for test
        'years': 0.1,  # Short duration for test
        'initial_capital': 10000
    }

    results = run_monte_carlo(config)

    # Should have 5 results
    assert len(results) == 5

    # Each result should have required fields
    for result in results:
        assert 'total_return' in result
        assert 'max_drawdown' in result
        assert 'total_trades' in result
        assert 'initial_capital' in result
        assert 'final_capital' in result

def test_run_monte_carlo_variability():
    """Test that different simulations produce different results"""
    config = {
        'simulations': 10,
        'years': 0.1,
        'initial_capital': 10000
    }

    results = run_monte_carlo(config)

    # Returns should vary (not all the same)
    returns = [r['total_return'] for r in results]
    unique_returns = set(returns)

    # With 10 simulations and randomness, should have multiple unique results
    assert len(unique_returns) > 1
```

**Step 2: Run tests to verify they fail**

```bash
cd /root/clawd && python -m pytest tests/test_monte_carlo.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backtest_system/monte_carlo.py
from backtest_system.data_generator import generate_price_path
from backtest_system.strategy_engine import run_backtest
from typing import List, Dict

def run_monte_carlo(config: dict) -> List[Dict]:
    """
    Run Monte Carlo simulation with multiple price paths.

    Args:
        config: Configuration dict with:
            - simulations: Number of simulations (default 100)
            - years: Years per simulation (default 1)
            - initial_capital: Starting capital (default 10000)
            - ... other strategy config

    Returns:
        List of result dicts, one per simulation
    """
    n_simulations = config.get('simulations', 100)
    years = config.get('years', 1)

    results = []

    for i in range(n_simulations):
        # Generate price path
        df = generate_price_path(years=years)

        # Run backtest
        result = run_backtest(df, config)

        results.append(result)

    return results
```

**Step 4: Run tests to verify they pass**

```bash
cd /root/clawd && python -m pytest tests/test_monte_carlo.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backtest_system/monte_carlo.py tests/test_monte_carlo.py
git commit -m "feat: implement Monte Carlo simulator"
```

---

## Task 6: Implement Analytics Module

**Files:**
- Modify: `backtest_system/analytics.py`
- Create: `tests/test_analytics.py`

**Step 1: Write the failing test**

```python
# tests/test_analytics.py
import numpy as np
from backtest_system.analytics import analyze_monte_carlo_results, calculate_confidence_interval

def test_calculate_confidence_interval():
    """Test confidence interval calculation"""
    data = [0.10, 0.15, 0.20, 0.25, 0.30]

    lower, upper = calculate_confidence_interval(data, confidence=0.95)

    # Should be a valid interval
    assert lower < upper
    assert lower > 0  # Lower should be positive for this data

def test_analyze_monte_carlo_results_basic():
    """Test basic analysis of Monte Carlo results"""
    results = [
        {'total_return': 0.20, 'max_drawdown': 0.15},
        {'total_return': 0.30, 'max_drawdown': 0.20},
        {'total_return': -0.10, 'max_drawdown': 0.25},
    ]

    stats = analyze_monte_carlo_results(results)

    # Should have average return
    assert 'avg_return' in stats
    assert abs(stats['avg_return'] - 0.1333) < 0.01  # (0.20 + 0.30 - 0.10) / 3

    # Should have return distribution
    assert 'return_ci_lower' in stats
    assert 'return_ci_upper' in stats

    # Should have drawdown stats
    assert 'avg_drawdown' in stats
    assert abs(stats['avg_drawdown'] - 0.20) < 0.01
```

**Step 2: Run tests to verify they fail**

```bash
cd /root/clawd && python -m pytest tests/test_analytics.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backtest_system/analytics.py
import numpy as np
from typing import List, Dict

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> tuple:
    """
    Calculate confidence interval for a dataset.

    Args:
        data: List of values
        confidence: Confidence level (default 0.95)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(data) < 2:
        return data[0] if data else 0, data[0] if data else 0

    arr = np.array(data)
    mean = np.mean(arr)
    std_err = np.std(arr, ddof=1) / np.sqrt(len(arr))

    # Use t-distribution for small samples
    from scipy import stats
    t_value = stats.t.ppf((1 + confidence) / 2, len(arr) - 1)

    margin = t_value * std_err

    return mean - margin, mean + margin

def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile value."""
    arr = np.array(data)
    return np.percentile(arr, percentile * 100)

def analyze_monte_carlo_results(results: List[Dict]) -> Dict:
    """
    Analyze Monte Carlo simulation results and compute statistics.

    Args:
        results: List of result dicts from run_monte_carlo

    Returns:
        Dict with comprehensive statistics
    """
    if not results:
        return {}

    # Extract returns
    returns = [r['total_return'] for r in results]
    drawdowns = [r['max_drawdown'] for r in results]
    trade_counts = [r['total_trades'] for r in results]
    win_rates = [r['win_rate'] for r in results if r['total_trades'] > 0]

    # Basic statistics
    stats = {
        'n_simulations': len(results),
        'avg_return': np.mean(returns),
        'std_return': np.std(returns, ddof=1),
        'median_return': np.median(returns),
        'best_return': np.max(returns),
        'worst_return': np.min(returns),
    }

    # Confidence intervals (95%)
    return_ci_lower, return_ci_upper = calculate_confidence_interval(returns, 0.95)
    stats['return_ci_lower'] = return_ci_lower
    stats['return_ci_upper'] = return_ci_upper

    # Percentiles
    stats['return_p5'] = calculate_percentile(returns, 0.05)
    stats['return_p25'] = calculate_percentile(returns, 0.25)
    stats['return_p75'] = calculate_percentile(returns, 0.75)
    stats['return_p95'] = calculate_percentile(returns, 0.95)

    # Drawdown statistics
    stats['avg_drawdown'] = np.mean(drawdowns)
    stats['max_drawdown_worst'] = np.max(drawdowns)
    stats['drawdown_ci_lower'], stats['drawdown_ci_upper'] = calculate_confidence_interval(drawdowns, 0.95)

    # Trade statistics
    stats['avg_trades'] = np.mean(trade_counts)
    if win_rates:
        stats['avg_win_rate'] = np.mean(win_rates)
    else:
        stats['avg_win_rate'] = 0

    # Profit factor
    profit_factors = [r['profit_factor'] for r in results if r['profit_factor'] > 0]
    if profit_factors:
        stats['avg_profit_factor'] = np.mean(profit_factors)
    else:
        stats['avg_profit_factor'] = 0

    # Sharpe ratio (simplified, using std of returns)
    if stats['std_return'] > 0:
        # Assume 2% risk-free rate annualized
        risk_free_rate = 0.02
        stats['sharpe_ratio'] = (stats['avg_return'] - risk_free_rate) / stats['std_return']
    else:
        stats['sharpe_ratio'] = 0

    return stats
```

**Step 4: Run tests to verify they pass**

```bash
cd /root/clawd && python -m pytest tests/test_analytics.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add backtest_system/analytics.py tests/test_analytics.py
git commit -m "feat: implement analytics with confidence intervals and statistics"
```

---

## Task 7: Implement Report Generator

**Files:**
- Modify: `backtest_system/reporter.py`

**Step 1: Write simple script to test (no unit test, just run and verify output)**

```python
# backtest_system/reporter.py
from backtest_system.analytics import analyze_monte_carlo_results

def format_percent(value: float, decimals: int = 1) -> str:
    """Format float as percentage string."""
    return f"{value * 100:.{decimals}f}%"

def generate_text_report(results: List[dict], stats: dict) -> str:
    """
    Generate formatted text report.

    Args:
        results: List of Monte Carlo results
        stats: Statistics from analyze_monte_carlo_results

    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 50)
    report.append("    趋势跟踪策略蒙特卡洛回测报告")
    report.append("=" * 50)
    report.append("")

    # 收益率统计
    report.append("📊 收益率统计")
    report.append(f"   平均年化收益: {format_percent(stats['avg_return'])}")
    report.append(f"   95%置信区间: {format_percent(stats['return_ci_lower'])} ~ {format_percent(stats['return_ci_upper'])}")
    report.append(f"   最佳收益: {format_percent(stats['best_return'])}")
    report.append(f"   最差收益: {format_percent(stats['worst_return'])}")
    report.append("")

    # 风险指标
    report.append("📉 风险指标")
    report.append(f"   平均最大回撤: {format_percent(stats['avg_drawdown'])}")
    report.append(f"   95%置信回撤: {format_percent(stats['drawdown_ci_lower'])} ~ {format_percent(stats['drawdown_ci_upper'])}")
    report.append(f"   夏普比率: {stats['sharpe_ratio']:.2f}")
    report.append("")

    # 交易质量
    report.append("🎯 交易质量")
    report.append(f"   平均交易次数: {stats['avg_trades']:.0f}次/模拟")
    report.append(f"   胜率: {format_percent(stats['avg_win_rate'])}")
    report.append(f"   盈亏比: {stats['avg_profit_factor']:.2f}")
    report.append("")

    report.append("=" * 50)

    return "\n".join(report)

def save_report_to_file(report: str, filepath: str):
    """Save report text to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
```

**Step 2: Create simple test script**

```bash
cat > /tmp/test_reporter.py << 'EOF'
from backtest_system.reporter import generate_text_report

# Create mock data
results = [
    {'total_return': 0.285, 'max_drawdown': 0.183, 'total_trades': 45, 'win_rate': 0.58, 'profit_factor': 1.85},
]

stats = {
    'avg_return': 0.285,
    'std_return': 0.20,
    'return_ci_lower': -0.15,
    'return_ci_upper': 0.65,
    'best_return': 0.82,
    'worst_return': -0.22,
    'avg_drawdown': 0.183,
    'drawdown_ci_lower': 0.12,
    'drawdown_ci_upper': 0.35,
    'sharpe_ratio': 1.42,
    'avg_trades': 45,
    'avg_win_rate': 0.58,
    'avg_profit_factor': 1.85,
}

report = generate_text_report(results, stats)
print(report)
EOF

python /tmp/test_reporter.py
```

Expected: Report printed with emoji and formatted values

**Step 3: Commit**

```bash
git add backtest_system/reporter.py
git commit -m "feat: implement text report generator"
```

---

## Task 8: Create Configuration File

**Files:**
- Modify: `backtest_system/config.json`

**Step 1: Create config file**

```json
{
  "simulations": 100,
  "years": 1,
  "initial_capital": 10000,

  "data": {
    "start_price": 100000,
    "volatility": 0.02,
    "drift": 0.0001
  },

  "strategy": {
    "lookback_bars": 60,
    "pivot_lookback": 10,
    "consolidation": {
      "min_bars": 2,
      "max_bars": 3,
      "max_range_percent": 0.01
    }
  },

  "risk": {
    "risk_percent": 0.02,
    "max_risk_positions": 3
  }
}
```

**Step 2: Commit**

```bash
git add backtest_system/config.json
git commit -m "chore: add configuration file"
```

---

## Task 9: Create Main Entry Script

**Files:**
- Create: `run_backtest.py`

**Step 1: Write main script**

```python
#!/usr/bin/env python3
"""
Main entry point for Monte Carlo backtesting system.
"""
import json
import sys
from backtest_system.monte_carlo import run_monte_carlo
from backtest_system.analytics import analyze_monte_carlo_results
from backtest_system.reporter import generate_text_report, save_report_to_file

def main():
    # Load config
    config_path = 'backtest_system/config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)

    print(f"Starting Monte Carlo simulation with {config['simulations']} iterations...")

    # Run Monte Carlo
    results = run_monte_carlo(config)

    print(f"Simulation complete. Analyzing results...")

    # Analyze results
    stats = analyze_monte_carlo_results(results)

    # Generate report
    report = generate_text_report(results, stats)

    # Print report
    print("\n")
    print(report)

    # Save report
    report_path = 'backtest_report.txt'
    save_report_to_file(report, report_path)
    print(f"\n✅ Report saved to {report_path}")

    # Save detailed results to JSON
    results_path = 'backtest_results.json'
    with open(results_path, 'w') as f:
        json.dump({
            'statistics': stats,
            'individual_results': results
        }, f, indent=2, default=str)
    print(f"✅ Detailed results saved to {results_path}")

if __name__ == '__main__':
    main()
```

**Step 2: Make executable and test**

```bash
chmod +x run_backtest.py
python run_backtest.py
```

Expected: Full simulation runs, report printed and saved

**Step 3: Commit**

```bash
git add run_backtest.py
git commit -m "feat: add main entry script"
```

---

## Task 10: Install Dependencies and Run Full Test

**Files:**
- Create: `requirements.txt`

**Step 1: Create requirements file**

```txt
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
```

**Step 2: Install dependencies**

```bash
pip install -r requirements.txt
```

**Step 3: Run full simulation**

```bash
python run_backtest.py
```

Expected: Complete simulation with 100 iterations, report generated

**Step 4: Verify outputs**

```bash
ls -la backtest_report.txt backtest_results.json
cat backtest_report.txt
```

**Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore: add requirements and verify full simulation"
```

---

## Task 11: Final Verification

**Step 1: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

**Step 2: Verify report format**

```bash
cat backtest_report.txt
```

Expected: Properly formatted report with emoji, percentages, and statistics

**Step 3: Verify JSON output**

```bash
head -50 backtest_results.json
```

Expected: Valid JSON with statistics and individual results

**Step 4: Commit final changes**

```bash
git add .
git commit -m "feat: complete Monte Carlo backtesting system"
```

---

**Plan complete and saved to `docs/plans/2026-02-10-trend-following-monte-carlo-backtest-implementation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
