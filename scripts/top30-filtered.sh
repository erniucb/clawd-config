#!/bin/bash
# 筛选后的交易量排名 - 剔除稳定币和重复币种

cd /root/clawd

echo "📊 **筛选后交易量排名（剔除稳定币和重复币种）** 📊"
echo "📅 $(date '+%Y/%m/%d %H:%M')"
echo ""

# 获取更多数据（前80）
response=$(curl -s "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=80&page=1&sparkline=false")

# 创建临时文件
temp_file=$(mktemp)

# 收集所有数据（包括交易量）
echo "$response" | jq -r '.[] | "\(.id)|\(.name)|\(.symbol)|\(.current_price)|\(.price_change_percentage_24h)|\(.total_volume)|\(.market_cap_rank)|\(.total_volume)"' > "$temp_file"

# 筛选并输出
awk -F'|' '
BEGIN {
  count = 0

  # 包装币ID映射到原生币ID
  wrapped["wbnb"] = "binancecoin"
  wrapped["wrapped-solana"] = "solana"
  wrapped["l2-standard-bridged-weth-base"] = "ethereum"
  wrapped["arbitrum-bridged-weth-arbitrum-one"] = "ethereum"
  wrapped["wrapped-ethereum"] = "ethereum"
  wrapped["weth"] = "ethereum"
  wrapped["wrapped-bitcoin"] = "bitcoin"
  wrapped["coinbase-wrapped-btc"] = "bitcoin"
  wrapped["binance-bitcoin"] = "bitcoin"
  wrapped["arbitrum-bridged-wbtc-arbitrum-one"] = "bitcoin"
  wrapped["wrapped-hype"] = "hyperliquid"
  wrapped["wrapped-avax"] = "avalanche-2"
  wrapped["wrapped-aave-ethereum-usdt"] = "ethereum"
  wrapped["wrapped-aave-ethereum-usdc"] = "ethereum"
}
{
  id = $1
  name = $2
  symbol = $3
  price = $4
  change = $5
  volume = $6
  rank = $7
  volume_num = $8

  # 检查是否是稳定币（价格在0.95-1.05之间）
  is_stablecoin = (price >= 0.95 && price <= 1.05)

  # 排除明显的稳定币关键词
  if (name ~ /USD|USDT|USDC|DAI|Tether|Stable|Circle|Pax|Ripple|RLUSD/) {
    is_stablecoin = 1
  }

  # 如果是稳定币，跳过
  if (is_stablecoin) {
    next
  }

  # 确定原生币ID
  native_id = id
  if (id in wrapped) {
    native_id = wrapped[id]
  }

  # 如果这个原生币已经有候选，比较交易量，保留大的
  if (native_id in best_volume) {
    if (volume_num > best_volume[native_id]) {
      best[native_id] = $0
      best_volume[native_id] = volume_num
    }
  } else {
    best[native_id] = $0
    best_volume[native_id] = volume_num
  }
}
END {
  # 提取所有选中的币
  for (native_id in best) {
    coins[count++] = best[native_id] "|" best_volume[native_id]
  }

  # 按交易量排序
  for (i = 0; i < count; i++) {
    split(coins[i], parts, "|")
    volumes[i] = parts[8]
    indices[i] = i
  }

  # 冒泡排序
  for (i = 0; i < count - 1; i++) {
    for (j = 0; j < count - i - 1; j++) {
      if (volumes[j+1] > volumes[j]) {
        temp = volumes[j]
        volumes[j] = volumes[j+1]
        volumes[j+1] = temp

        temp = indices[j]
        indices[j] = indices[j+1]
        indices[j+1] = temp
      }
    }
  }

  # 输出前30个
  for (i = 0; i < 30 && i < count; i++) {
    print coins[indices[i]]
  }
}
' "$temp_file" | while IFS='|' read -r id name symbol price change volume rank extra_volume volume_num; do

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

# 清理临时文件
rm -f "$temp_file"

echo ""
echo "=== 数据来源: CoinGecko API ==="
echo "已剔除: 稳定币（价格接近$1）和包装代币（对于重复币种，保留交易量最大的）"
