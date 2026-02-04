#!/bin/bash
# 生成BTC 4小时K线图

echo "📊 BTC/USD 4小时K线图（最近30根）"
echo "📅 $(date '+%Y/%m/%d %H:%M')"
echo ""

# 获取小时数据并合并为4小时K线
data=$(curl -s "https://min-api.cryptocompare.com/data/v2/histohour?fsym=BTC&tsym=USD&limit=120")

# 提取并处理数据
echo "$data" | jq -r '.Data.Data | reverse | .[] | "\(.time) \(.open) \(.high) \(.low) \(.close)"' | awk '
BEGIN {
  count = 0
  max_high = 0
  min_low = 999999999
  candles = ""
}

{
  time = $1
  open_val = $2
  high_val = $3
  low_val = $4
  last_close = $5

  if (count == 0) {
    interval_start = int(time / 3600 / 4) * 4 * 3600
    c_open = open_val
    c_high = high_val
    c_low = low_val
  }

  if (high_val > c_high) c_high = high_val
  if (low_val < c_low) c_low = low_val
  c_last_close = last_close

  count++

  if (count == 4) {
    candles = candles sprintf("%s %s %s %s %s\n", c_open, c_high, c_low, c_last_close, interval_start)

    if (c_high > max_high) max_high = c_high
    if (c_low < min_low) min_low = c_low

    count = 0
  }
}

END {
  if (count > 0) {
    candles = candles sprintf("%s %s %s %s %s\n", c_open, c_high, c_low, c_last_close, interval_start)
    if (c_high > max_high) max_high = c_high
    if (c_low < min_low) min_low = c_low
  }

  printf "价格范围: $%.2f - $%.2f\n", min_low, max_high
  printf "\n"

  split(candles, lines, "\n")
  count_lines = 0
  for (i in lines) {
    if (lines[i] != "") count_lines++
  }

  # 输出最近30根
  recent_count = 0
  for (i = count_lines - 1; i >= 0 && recent_count < 30; i--) {
    split(lines[i], parts, " ")
    open_val = parts[1]
    high_val = parts[2]
    low_val = parts[3]
    close_val = parts[4]
    time_val = parts[5]

    # 计算高度
    range = max_high - min_low
    high_height = int((high_val - min_low) / range * 25) + 1
    low_height = int((low_val - min_low) / range * 25) + 1
    close_height = int((close_val - min_low) / range * 25) + 1
    open_height = int((open_val - min_low) / range * 25) + 1

    # 涨跌颜色
    change = (close_val - open_val) / open_val * 100
    color = (change >= 0) ? "🟢" : "🔴"

    # 简化的K线显示
    printf "%2d. ", recent_count + 1

    # 绘制K线柱
    for (j = 1; j < low_height; j++) printf " "
    for (j = low_height; j <= high_height; j++) printf "█"

    printf " %s %.0f → %.0f (%.2f%%)\n", color, open_val, close_val, change

    recent_count++
  }
}
'

echo ""
echo "📈 数据来源: CryptoCompare API"
echo "K线周期: 4小时"
echo "每根 █ 代表价格变化区间"
