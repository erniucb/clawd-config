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
