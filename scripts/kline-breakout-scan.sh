#!/bin/bash
# 4小时K线突破检测脚本（使用CryptoCompare API - 最终版）

cd /root/clawd

# 配置参数
INTERVAL_HOURS=4          # K线周期（小时）
LOOKBACK_CANDLES=30        # 回溯K线数量（用于识别震荡区间）
BREAKOUT_THRESHOLD=0.03   # 突破阈值（3%）
RANGE_THRESHOLD=0.15       # 震荡区间阈值（15%，区间宽度/最低价）

# 币种符号映射（CoinGecko ID -> CryptoCompare Symbol）
declare -A COIN_MAP=(
  ["bitcoin"]="BTC"
  ["ethereum"]="ETH"
  ["solana"]="SOL"
  ["ripple"]="XRP"
  ["dogecoin"]="DOGE"
  ["binancecoin"]="BNB"
  ["tron"]="TRX"
  ["sui"]="SUI"
  ["cardano"]="ADA"
  ["chainlink"]="LINK"
  ["litecoin"]="LTC"
  ["zcash"]="ZEC"
  ["pepe"]="PEPE"
  ["aave"]="AAVE"
  ["bitcoin-cash"]="BCH"
  ["avalanche-2"]="AVAX"
  ["uniswap"]="UNI"
  ["near"]="NEAR"
  ["polkadot"]="DOT"
  ["monero"]="XMR"
  ["stellar"]="XLM"
  ["ankr"]="ANKR"
  ["hedera-hashgraph"]="HBAR"
  ["arbitrum"]="ARB"
  ["dogwifhat"]="WIF"
  ["dash"]="DASH"
  ["bittensor"]="TAO"
  ["toncoin"]="TON"
  ["filecoin"]="FIL"
  ["layerzero"]="ZRO"
)

echo "📊 4小时K线突破检测"
echo "📅 $(date '+%Y/%m/%d %H:%M')"
echo ""

# 需要获取的小时数据量
TOTAL_HOURS=$((LOOKBACK_CANDLES * INTERVAL_HOURS + 24))
DATA_LIMIT=$((TOTAL_HOURS + 10))

for coin_id in "${!COIN_MAP[@]}"; do
  symbol="${COIN_MAP[$coin_id]}"

  # 获取小时K线数据
  response=$(curl -s "https://min-api.cryptocompare.com/data/v2/histohour?fsym=${symbol}&tsym=USD&limit=${DATA_LIMIT}")

  # 检查响应是否有效
  if ! echo "$response" | jq -e '.Data.Data' > /dev/null 2>&1; then
    continue
  fi

  # 提取并处理数据（时间顺序）
  klines=$(echo "$response" | jq -r '.Data.Data | reverse | .[] | "\(.time) \(.open) \(.high) \(.low) \(.close)"')

  # 计算K线（将小时K线合并为4小时K线）
  declare -a candles
  interval_start=0
  candle_open=0
  candle_high=0
  candle_low=999999999
  candle_close=0
  count=0

  while IFS=' ' read -r time open_price high_price low_price last_close; do
    # 每隔4小时开始新的K线
    if [ $count -eq 0 ]; then
      interval_start=$((time / 3600 / INTERVAL_HOURS * INTERVAL_HOURS * 3600))
      candle_open=$open_price
      candle_high=$high_price
      candle_low=$low_price
    fi

    # 更新高低价
    high_check=$(echo "$high_price $candle_high" | awk '{if ($1 > $2) print 1; else print 0}')
    low_check=$(echo "$low_price $candle_low" | awk '{if ($1 < $2) print 1; else print 0}')

    if [ "$high_check" = "1" ]; then
      candle_high=$high_price
    fi
    if [ "$low_check" = "1" ]; then
      candle_low=$low_price
    fi
    candle_close=$last_close

    count=$((count + 1))

    # 每4小时输出一根K线
    if [ $count -eq $INTERVAL_HOURS ]; then
      candles+=("$candle_open|$candle_high|$candle_low|$candle_close|$interval_start")
      count=0
    fi
  done <<< "$klines"

  # 处理最后一根K线
  if [ $count -gt 0 ]; then
    candles+=("$candle_open|$candle_high|$candle_low|$candle_close|$interval_start")
  fi

  candle_count=${#candles[@]}

  # 检查是否有足够的K线数据
  if [ $candle_count -lt $((LOOKBACK_CANDLES + 1)) ]; then
    continue
  fi

  # 提取回溯K线（不包括最后一根）
  range_high=0
  range_low=999999999

  for ((i = candle_count - LOOKBACK_CANDLES - 1; i < candle_count - 1; i++)); do
    IFS='|' read -r t_open t_high t_low t_close t_timestamp <<< "${candles[$i]}"

    # 使用awk进行比较
    high_check=$(echo "$t_high $range_high" | awk '{if ($1 > $2) print 1; else print 0}')
    low_check=$(echo "$t_low $range_low" | awk '{if ($1 < $2) print 1; else print 0}')

    if [ "$high_check" = "1" ]; then
      range_high=$t_high
    fi
    if [ "$low_check" = "1" ]; then
      range_low=$t_low
    fi
  done

  # 获取最后一根K线
  last_candle="${candles[$((candle_count - 1))]}"
  IFS='|' read -r t_open t_high t_low t_close t_timestamp <<< "$last_candle"

  # 判断是否震荡（区间宽度 < 阈值）
  range_width=$(awk -v high="$range_high" -v low="$range_low" 'BEGIN {printf "%.2f", (high - low) / low * 100}')
  range_limit=$(awk -v threshold="$RANGE_THRESHOLD" 'BEGIN {printf "%.2f", threshold * 100}')
  is_sideways=$(awk -v width="$range_width" -v limit="$range_limit" 'BEGIN {if (width < limit) print 1; else print 0}')

  # 如果是震荡，检查突破
  if [ "$is_sideways" = "1" ]; then
    # 计算突破阈值
    breakout_up=$(awk -v high="$range_high" -v threshold="$BREAKOUT_THRESHOLD" 'BEGIN {printf "%.2f", high * (1 + threshold)}')
    breakout_down=$(awk -v low="$range_low" -v threshold="$BREAKOUT_THRESHOLD" 'BEGIN {printf "%.2f", low * (1 - threshold)}')

    # 检查是否向上突破
    breakout_up_check=$(awk -v last_close="$t_close" -v breakout="$breakout_up" 'BEGIN {if (last_close > breakout) print 1; else print 0}')
    if [ "$breakout_up_check" = "1" ]; then
      change=$(awk -v last_close="$t_close" -v high="$range_high" 'BEGIN {printf "%.2f", (last_close - high) / high * 100}')
      echo "🚀 向上突破: $coin_id ($symbol)"
      echo "   收盘价: \$$t_close"
      echo "   突破区间: \$$range_low - \$$range_high"
      echo "   区间宽度: ${range_width}%"
      echo "   突破幅度: +${change}%"
      echo ""
    fi

    # 检查是否向下突破
    breakout_down_check=$(awk -v last_close="$t_close" -v breakout="$breakout_down" 'BEGIN {if (last_close < breakout) print 1; else print 0}')
    if [ "$breakout_down_check" = "1" ]; then
      change=$(awk -v last_close="$t_close" -v low="$range_low" 'BEGIN {printf "%.2f", (low - last_close) / low * 100}')
      echo "💥 向下突破: $coin_id ($symbol)"
      echo "   收盘价: \$$t_close"
      echo "   突破区间: \$$range_low - \$$range_high"
      echo "   区间宽度: ${range_width}%"
      echo "   突破幅度: -${change}%"
      echo ""
    fi
  fi

done

echo "=== 检测完成 ==="
echo "参数: ${INTERVAL_HOURS}小时K线, 回溯${LOOKBACK_CANDLES}根, 震荡阈值${RANGE_THRESHOLD}%, 突破阈值${BREAKOUT_THRESHOLD}%"
echo "数据来源: CryptoCompare API"
