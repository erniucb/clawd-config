#!/bin/bash
# 币安价格监控脚本 - 使用REST API获取价格

cd /root/clawd

# 配置要监控的交易对
SYMBOLS=("BTCUSDT" "ETHUSDT" "SOLUSDT" "DOGEUSDT" "BNBUSDT")

# API端点
API_URL="https://api.binance.com/api/v3/ticker/price"

echo "=== 币安价格监控 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 获取所有交易对的价格
for symbol in "${SYMBOLS[@]}"; do
  # 获取价格
  price=$(curl -s "${API_URL}?symbol=${symbol}" | jq -r '.price')

  # 获取24小时变化（使用另一个API）
  ticker_24h=$(curl -s "https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}")

  change_percent=$(echo $ticker_24h | jq -r '.priceChangePercent')
  high=$(echo $ticker_24h | jq -r '.highPrice')
  low=$(echo $ticker_24h | jq -r '.lowPrice')

  # 格式化价格（保留2位小数）
  formatted_price=$(printf "%.2f" $price)

  # 判断涨跌颜色（终端输出）
  if (( $(echo "$change_percent > 0" | bc -l) )); then
    arrow="📈"
  elif (( $(echo "$change_percent < 0" | bc -l) )); then
    arrow="📉"
  else
    arrow="➡️"
  fi

  echo "$symbol: $formatted_price USDT $arrow ${change_percent}%"
  echo "  24h高: $high | 24h低: $low"
  echo ""
done

echo "=== 数据来源: Binance API ==="
