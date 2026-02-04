#!/bin/bash
# 获取按交易量排名前30的加密货币

cd /root/clawd

echo "=== 获取交易量排名前30的币种 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 获取数据
API_URL="https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=30&page=1&sparkline=false"

response=$(curl -s "$API_URL")

# 保存数据
mkdir -p /root/clawd/data
echo "$response" > /root/clawd/data/crypto_top30_volume.json

# 解析并显示
echo "📊 **交易量排名前30币种** 📊"
echo ""

# 使用jq解析
echo "$response" | jq -r '.[] | "\(.market_cap_rank | tostring + "." | ljust(4)) \(.name | ljust(20)) \(.symbol | ascii_upcase | ljust(10)) 价格: $\(.current_price | tostring | tonumber | if . < 1 then (.* 1000000 | round / 1000000 | tostring) else (.* 100 | round / 100 | tostring) end) | 24h涨跌: \(.price_change_percentage_24h | tostring + "%") | 24h交易量: $\(.total_volume | tonumber | if . >= 1000000000 then (. / 1000000000 | floor | tostring + "B") elif . >= 1000000 then (. / 1000000 | floor | tostring + "M") elif . >= 1000 then (. / 1000 | floor | tostring + "K") else tostring end)"' | while read line; do
  # 解析涨跌百分比
  if [[ $line == *"-"*"%"* ]]; then
    echo "🔴 $line"
  else
    echo "🟢 $line"
  fi
done

echo ""
echo "=== 数据来源: CoinGecko API ==="
echo "✅ 数据已保存到: /root/clawd/data/crypto_top30_volume.json"
