#!/bin/bash
# 4小时K线突破检测脚本（简化版）

cd /root/clawd

# 配置参数
INTERVAL_HOURS=4          # K线周期（小时）
LOOKBACK_CANDLES=30        # 回溯K线数量（用于识别震荡区间）
BREAKOUT_THRESHOLD=0.03   # 突破阈值（3%）
RANGE_THRESHOLD=0.15       # 震荡区间阈值（15%，区间宽度/最低价）

# 币种ID列表（前10个测试）
COIN_IDS=(
  "bitcoin"
  "ethereum"
  "solana"
  "ripple"
  "dogecoin"
  "binancecoin"
  "pax-gold"
  "hyperliquid"
  "tron"
  "sui"
)

echo "📊 4小时K线突破检测（测试版-仅前10个币）"
echo "📅 $(date '+%Y/%m/%d %H:%M')"
echo ""

debug_count=0

for coin_id in "${COIN_IDS[@]}"; do

  # 获取价格数据
  response=$(curl -s "https://api.coingecko.com/api/v3/coins/${coin_id}/market_chart?vs_currency=usd&days=7")

  # 检查响应是否有效
  if ! echo "$response" | jq -e '.prices' > /dev/null 2>&1; then
    continue
  fi

  # 提取价格数据并反转
  prices=$(echo "$response" | jq -r '.prices | reverse | .[] | "\([0]) \([1])"')

  # 临时文件存储K线数据
  candle_file=$(mktemp)

  # 简化处理：将每4个小时的数据作为一根K线（取每小时最后一个价格）
  echo "$prices" | awk -v interval=$INTERVAL_HOURS '
  BEGIN {
    count = 0
    first = 1
    last_close = 0
  }
  {
    timestamp = $1
    price = $2

    if (first) {
      first_timestamp = timestamp
      first = 0
    }

    # 计算当前小时数
    current_hour = int(timestamp / 1000 / 3600)

    if (count == 0) {
      start_hour = current_hour
      open = price
      high = price
      low = price
      close = price
      start_time = timestamp
    }

    # 更新高低价
    if (price > high) high = price
    if (price < low) low = price
    last_price = price

    count++

    # 每4小时输出一根K线
    if (current_hour - start_hour >= interval || count >= 100) {
      print open "|" high "|" low "|" last_price "|" start_time
      count = 0
      start_hour = current_hour
    }
  }
  # 输出最后一根K线
  END {
    if (count > 0) {
      print open "|" high "|" low "|" last_price "|" start_time
    }
  }
  ' > "$candle_file"

  # 读取K线数据
  candle_count=$(wc -l < "$candle_file")

  # 检查是否有足够的K线数据
  if [ $candle_count -lt $((LOOKBACK_CANDLES + 1)) ]; then
    rm -f "$candle_file"
    continue
  fi

  # 提取回溯K线（不包括最后一根）
  range_high=0
  range_low=999999999

  tail -n $((LOOKBACK_CANDLES)) "$candle_file" | head -n $((LOOKBACK_CANDLES - 1)) | while IFS='|' read -r open high low close timestamp; do

    # 使用awk进行比较，避免bc错误
    high_check=$(echo "$high" "$range_high" | awk '{if ($1 > $2) print 1; else print 0}')
    low_check=$(echo "$low" "$range_low" | awk '{if ($1 < $2) print 1; else print 0}')

    if [ "$high_check" = "1" ]; then
      range_high=$high
    fi
    if [ "$low_check" = "1" ]; then
      range_low=$low
    fi
  done

  # 获取最后一根K线
  last_candle=$(tail -n 1 "$candle_file")
  IFS='|' read -r last_open last_high last_low last_close last_timestamp <<< "$last_candle"

  # 清理临时文件
  rm -f "$candle_file"

  # 调试：显示区间信息
  debug_count=$((debug_count + 1))
  echo "DEBUG $debug_count: $coin_id"
  echo "  回溯区间: \$$range_low - \$$range_high"
  echo "  最新收盘: \$$last_close"
  echo "  K线数量: $candle_count"
  echo ""

done

echo "=== 检测完成 ==="
echo "参数: ${INTERVAL_HOURS}小时K线, 回溯${LOOKBACK_CANDLES}根, 震荡阈值${RANGE_THRESHOLD}%, 突破阈值${BREAKOUT_THRESHOLD}%"
