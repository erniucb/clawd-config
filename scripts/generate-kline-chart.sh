#!/bin/bash
# 生成BTC日K线图

echo "📊 BTC/USD 日K线图（最近30天）"
echo "📅 $(date '+%Y/%m/%d')"
echo ""

# 获取数据
data=$(curl -s "https://min-api.cryptocompare.com/data/v2/histoday?fsym=BTC&tsym=USD&limit=30")

# 提取价格数据
prices=$(echo "$data" | jq -r '.Data.Data | reverse | .[] | .close')

# 计算高低价
max_price=$(echo "$prices" | sort -rn | head -1)
min_price=$(echo "$prices" | sort -n | head -1)

# 生成图表
echo "价格范围: \$$min_price - \$$max_price"
echo ""
echo "价格走势图:"
echo ""

# 使用ASCII字符绘制
echo "$prices" | nl -v 1 -s '. ' | awk -v max="$max_price" -v min="$min_price" '
{
  line_num = $1
  price = $2

  # 计算相对高度（0-40列）
  range = max - min
  height = int((price - min) / range * 38)

  # 生成柱状图
  bars = ""
  for (i = 0; i < height; i++) {
    bars = bars "█"
  }

  printf "%2d. %-8s %s $%.0f\n", line_num, bars, (height < 38 ? ">" : ""), price
}
'

echo ""
echo "📈 数据来源: CryptoCompare"
