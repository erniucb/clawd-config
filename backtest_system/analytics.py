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
