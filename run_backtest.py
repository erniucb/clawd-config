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
