#!/usr/bin/env python3
"""Quick test run with fewer simulations"""
import json
from backtest_system.monte_carlo import run_monte_carlo
from backtest_system.analytics import analyze_monte_carlo_results
from backtest_system.reporter import generate_text_report, save_report_to_file

# Quick config with fewer simulations for testing
config = {
    'simulations': 10,  # Only 10 for quick test
    'years': 0.5,  # 6 months
    'initial_capital': 10000,

    'data': {
        'start_price': 100000,
        'volatility': 0.02,
        'drift': 0.0001
    },

    'strategy': {
        'lookback_bars': 60,
        'pivot_lookback': 10,
        'consolidation': {
            'min_bars': 2,
            'max_bars': 3,
            'max_range_percent': 0.01
        }
    },

    'risk': {
        'risk_percent': 0.02,
        'max_risk_positions': 3
    }
}

print(f"Starting quick test with {config['simulations']} simulations...")

results = run_monte_carlo(config)
print(f"Simulation complete. Analyzing...")

stats = analyze_monte_carlo_results(results)
report = generate_text_report(results, stats)

print("\n" + report)

report_path = 'backtest_report_quick.txt'
save_report_to_file(report, report_path)
print(f"\n✅ Report saved to {report_path}")

results_path = 'backtest_results_quick.json'
with open(results_path, 'w') as f:
    json.dump({'statistics': stats, 'individual_results': results}, f, indent=2, default=str)
print(f"✅ Results saved to {results_path}")
