#!/bin/bash
# Twitter热点追踪 - 完整版（扫描+发送报告）

cd /root/clawd

echo "=== Twitter Web3热点追踪器 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M')"
echo ""

# 步骤1: 扫描Twitter
echo "📡 步骤1: 扫描Twitter时间线..."
bash /root/clawd/scripts/twitter-hotspot-scan.sh > /tmp/hotspot-scan.log 2>&1

# 步骤2: 发送报告
echo ""
echo "📱 步骤2: 发送热点报告..."
python3 /root/clawd/scripts/send-hotspot-report.py >> /tmp/hotspot-report.log 2>&1

echo ""
echo "=== ✅ 完成 ==="
echo ""
echo "📊 热点报告已发送到你的Telegram"
echo ""
echo "💡 提示："
echo "  - 发送 'twitter scan' 可以立即重新扫描"
echo "  - 每天中午12点会自动发送"
