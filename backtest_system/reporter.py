from typing import List
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
