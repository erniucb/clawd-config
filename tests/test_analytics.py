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
        {'total_return': 0.20, 'max_drawdown': 0.15, 'total_trades': 10, 'win_rate': 0.6, 'profit_factor': 1.5},
        {'total_return': 0.30, 'max_drawdown': 0.20, 'total_trades': 15, 'win_rate': 0.7, 'profit_factor': 1.8},
        {'total_return': -0.10, 'max_drawdown': 0.25, 'total_trades': 5, 'win_rate': 0.4, 'profit_factor': 0.8},
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
