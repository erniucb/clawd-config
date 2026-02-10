from backtest_system.monte_carlo import run_monte_carlo

def test_run_monte_carlo_returns_results():
    """Test that Monte Carlo simulation returns correct number of results"""
    config = {
        'simulations': 2,  # Minimal for quick test
        'years': 0.1,  # Short duration for test
        'initial_capital': 10000,
        'lookback_bars': 20,  # Reduced lookback for faster testing
        'pivot_lookback': 3   # Reduced pivot lookback
    }

    results = run_monte_carlo(config)

    # Should have 2 results
    assert len(results) == 2

    # Each result should have required fields
    for result in results:
        assert 'total_return' in result
        assert 'max_drawdown' in result
        assert 'total_trades' in result
        assert 'initial_capital' in result
        assert 'final_capital' in result

def test_run_monte_carlo_variability():
    """Test that Monte Carlo can run multiple times"""
    config = {
        'simulations': 2,  # Minimal for quick test
        'years': 0.05,  # Very short for quick test
        'initial_capital': 10000,
        'lookback_bars': 20,
        'pivot_lookback': 3
    }

    results = run_monte_carlo(config)

    # Check we got results
    assert len(results) == 2

    # Each result should have valid data
    for result in results:
        assert isinstance(result['total_return'], (int, float))
        assert isinstance(result['max_drawdown'], (int, float))
        assert isinstance(result['total_trades'], int)
