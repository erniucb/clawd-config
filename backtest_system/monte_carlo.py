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
