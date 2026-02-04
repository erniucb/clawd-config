#!/bin/bash
# 显示交易量排名前30的币种

cd /root/clawd

echo "📊 **交易量排名前30币种** 📊"
echo "📅 $(date '+%Y/%m/%d %H:%M')"
echo ""

# 获取数据
response=$(curl -s "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=30&page=1&sparkline=false")

# 使用jq逐条输出
echo "$response" | jq -r '.[] | "\(.market_cap_rank)|\(.name)|\(.symbol)|\(.current_price)|\(.price_change_percentage_24h)|\(.total_volume)"' | while IFS='|' read -r rank name symbol price change volume; do

  # 格式化价格
  if (( $(echo "$price < 1" | bc -l 2>/dev/null || echo "0") )); then
    formatted_price=$(printf "%.6f" $price)
  else
    formatted_price=$(printf "%.2f" $price)
  fi

  # 格式化交易量
  if (( $(echo "$volume >= 1000000000" | bc -l 2>/dev/null || echo "0") )); then
    vol_formatted=$(echo "scale=1; $volume / 1000000000" | bc)
    vol_str="${vol_formatted}B"
  elif (( $(echo "$volume >= 1000000" | bc -l 2>/dev/null || echo "0") )); then
    vol_formatted=$(echo "scale=1; $volume / 1000000" | bc)
    vol_str="${vol_formatted}M"
  else
    vol_formatted=$(echo "scale=0; $volume / 1000" | bc)
    vol_str="${vol_formatted}K"
  fi

  # 判断涨跌
  if (( $(echo "$change > 0" | bc -l 2>/dev/null || echo "0") )); then
    color="🟢"
    change_str="+${change}%"
  elif (( $(echo "$change < 0" | bc -l 2>/dev/null || echo "0") )); then
    color="🔴"
    change_str="${change}%"
  else
    color="⚪"
    change_str="0.00%"
  fi

  # 输出格式化后的信息
  printf "%s #%-3s %-20s %-8s $\%-12s 24h: %-8s Vol: \$%s\n" \
    "$color" \
    "$rank" \
    "${name:0:20}" \
    "$(echo $symbol | tr '[:lower:]' '[:upper:]')" \
    "$formatted_price" \
    "$change_str" \
    "$vol_str"

done

echo ""
echo "=== 数据来源: CoinGecko API ==="
