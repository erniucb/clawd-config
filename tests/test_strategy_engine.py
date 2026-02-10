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

    # Add 3 risky positions (stop_loss < entry_price)
    for i in range(3):
        pos = Position(entry_price=105+i, stop_loss=100+i, initial_capital=10000, risk_percent=0.02)
        portfolio.add_position(pos)

    # Should have exactly 3 risky positions
    assert portfolio.get_risky_count() == 3

    # Should not allow 4th risky position
    pos4 = Position(entry_price=115, stop_loss=110, initial_capital=10000, risk_percent=0.02)
    assert portfolio.can_open_position(pos4) == False

    # Add a safe position (stop_loss >= entry_price)
    # Safe positions can be added without checking risk limit
    safe_pos = Position(entry_price=100, stop_loss=90, initial_capital=10000, risk_percent=0.02)
    safe_pos.update_stop_loss(100)  # Make it safe
    portfolio.add_position(safe_pos)

    # Should still have only 3 risky positions (safe position doesn't count)
    assert portfolio.get_risky_count() == 3

    # Safe positions themselves can always be opened
    another_safe = Position(entry_price=90, stop_loss=80, initial_capital=10000, risk_percent=0.02)
    another_safe.update_stop_loss(90)
    assert portfolio.can_open_position(another_safe) == True
