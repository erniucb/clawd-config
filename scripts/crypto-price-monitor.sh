#!/bin/bash
# 加密货币价格监控脚本 - 使用CoinGecko API

cd /root/clawd

# 配置要监控的币种（CoinGecko ID映射）
# 格式: "显示名称|CoinGecko_ID"
COINS=(
  "Bitcoin|bitcoin"
  "Ethereum|ethereum"
  "Solana|solana"
  "Dogecoin|dogecoin"
  "BNB|binancecoin"
)

# API端点
API_URL="https://api.coingecko.com/api/v3/simple/price"

echo "=== 加密货币价格监控 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 构建ID列表
coin_ids=""
for coin_info in "${COINS[@]}"; do
  id=$(echo $coin_info | cut -d'|' -f2)
  if [ -z "$coin_ids" ]; then
    coin_ids="$id"
  else
    coin_ids="$coin_ids,$id"
  fi
done

# 获取价格数据
response=$(curl -s "${API_URL}?ids=${coin_ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true")

# 解析并显示
for coin_info in "${COINS[@]}"; do
  name=$(echo $coin_info | cut -d'|' -f1)
  id=$(echo $coin_info | cut -d'|' -f2)

  # 使用jq提取数据
  price=$(echo $response | jq -r ".${id}.usd")
  change=$(echo $response | jq -r ".${id}.usd_24h_change")
  market_cap=$(echo $response | jq -r ".${id}.usd_market_cap")

  # 判断是否成功获取数据
  if [ "$price" != "null" ] && [ "$price" != "" ]; then
    # 格式化价格
    if (( $(echo "$price < 1" | bc -l 2>/dev/null || echo "0") )); then
      formatted_price=$(printf "%.6f" $price)
    else
      formatted_price=$(printf "%.2f" $price)
    fi

    # 判断涨跌
    if (( $(echo "$change > 0" | bc -l 2>/dev/null || echo "0") )); then
      arrow="📈"
      color="🟢"
    elif (( $(echo "$change < 0" | bc -l 2>/dev/null || echo "0") )); then
      arrow="📉"
      color="🔴"
    else
      arrow="➡️"
      color="⚪"
    fi

    # 格式化市值
    if [ "$market_cap" != "null" ] && [ "$market_cap" != "" ]; then
      if (( $(echo "$market_cap >= 1000000000" | bc -l 2>/dev/null || echo "0") )); then
        mc_formatted=$(echo "scale=2; $market_cap / 1000000000" | bc)
        mc_str="${mc_formatted}B"
      elif (( $(echo "$market_cap >= 1000000" | bc -l 2>/dev/null || echo "0") )); then
        mc_formatted=$(echo "scale=2; $market_cap / 1000000" | bc)
        mc_str="${mc_formatted}M"
      else
        mc_formatted=$(echo "scale=2; $market_cap / 1000" | bc)
        mc_str="${mc_formatted}K"
      fi
    else
      mc_str="N/A"
    fi

    echo "$color $name: \$$formatted_price"
    echo "   ${arrow} 24h: ${change}% | 市值: \$$mc_str"
    echo ""
  else
    echo "❌ $name: 获取失败"
    echo ""
  fi
done

echo "=== 数据来源: CoinGecko API ==="
