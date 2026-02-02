#!/usr/bin/env python3
"""
Twitter热点报告发送脚本
定时发送Web3热点报告到Telegram
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def send_telegram_message(message: str):
    """通过Clawdbot发送Telegram消息"""
    # 使用echo命令触发消息（因为小桃不能直接调自己的API）
    cmd = f'echo "{message}" | tail -1'
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("消息已发送")
    except Exception as e:
        print(f"发送失败: {e}")

def load_hotspot_data() -> dict:
    """加载热点数据"""
    data_file = Path('/root/clawd/data/twitter_hotspots.json')
    if not data_file.exists():
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_report(data: dict) -> str:
    """格式化报告"""
    if not data:
        return "📊 Twitter Web3热点报告\n\n❌ 今天没有扫描到数据"
    
    report = "📊 Twitter Web3热点报告\n"
    report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    if data.get('high_potential_count', 0) > 0:
        report += f"🔥 发现 {data['high_potential_count']} 个高潜力热点！\n\n"
    
    if data.get('medium_potential_count', 0) > 0:
        report += f"⭐ 发现 {data['medium_potential_count']} 个中潜力热点！\n\n"
    
    if 'stats' in data:
        stats = data['stats']
        report += "📊 统计信息：\n"
        if stats.get('airdrop', 0) > 0:
            report += f"  🎁 空投相关: {stats['airdrop']}个\n"
        if stats.get('new_project', 0) > 0:
            report += f"  🚀 新项目: {stats['new_project']}个\n"
        if stats.get('funding', 0) > 0:
            report += f"  💰 融资信息: {stats['funding']}个\n"
        if stats.get('defi', 0) > 0:
            report += f"  💧 DeFi: {stats['defi']}个\n"
        if stats.get('nft', 0) > 0:
            report += f"  🖼️ NFT: {stats['nft']}个\n"
    
    report += "\n💡 提示: 发送 'twitter scan' 命令可以立即扫描热点"
    
    return report

def main():
    print(f"正在准备热点报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 加载数据
    data = load_hotspot_data()
    
    # 格式化报告
    report = format_report(data)
    
    print("\n=== 报告内容 ===")
    print(report)
    print("\n=== 准备发送 ===")
    
    # 发送到Telegram
    send_telegram_message(report)

if __name__ == "__main__":
    main()
