#!/bin/bash
# 4小时K线突破检测 - 邮件通知版

cd /root/clawd

# 配置参数
INTERVAL_HOURS=4
LOOKBACK_CANDLES=30
BREAKOUT_THRESHOLD=0.01   # 突破阈值1%
RANGE_THRESHOLD=0.15       # 震荡区间阈值15%

# 币种符号映射
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

EMAIL_RECIPIENT="371398370@qq.com"

TOTAL_HOURS=$((LOOKBACK_CANDLES * INTERVAL_HOURS + 24))
DATA_LIMIT=$((TOTAL_HOURS + 10))

breakup_coins=""
breakdown_coins=""
breakup_details=""
breakdown_details=""

for coin_id in "${!COIN_MAP[@]}"; do
  symbol="${COIN_MAP[$coin_id]}"

  response=$(curl -s "https://min-api.cryptocompare.com/data/v2/histohour?fsym=${symbol}&tsym=USD&limit=${DATA_LIMIT}")

  if ! echo "$response" | jq -e '.Data.Data' > /dev/null 2>&1; then
    continue
  fi

  klines=$(echo "$response" | jq -r '.Data.Data | reverse | .[] | "\(.time) \(.open) \(.high) \(.low) \(.close)"')

  declare -a candles
  interval_start=0
  candle_open=0
  candle_high=0
  candle_low=999999999
  candle_close=0
  count=0

  while IFS=' ' read -r time open_price high_price low_price last_close; do
    if [ $count -eq 0 ]; then
      interval_start=$((time / 3600 / INTERVAL_HOURS * INTERVAL_HOURS * 3600))
      candle_open=$open_price
      candle_high=$high_price
      candle_low=$low_price
    fi

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

    if [ $count -eq $INTERVAL_HOURS ]; then
      candles+=("$candle_open|$candle_high|$candle_low|$candle_close|$interval_start")
      count=0
    fi
  done <<< "$klines"

  if [ $count -gt 0 ]; then
    candles+=("$candle_open|$candle_high|$candle_low|$candle_close|$interval_start")
  fi

  candle_count=${#candles[@]}

  if [ $candle_count -lt $((LOOKBACK_CANDLES + 1)) ]; then
    continue
  fi

  range_high=0
  range_low=999999999

  for ((i = candle_count - LOOKBACK_CANDLES - 1; i < candle_count - 1; i++)); do
    IFS='|' read -r t_open t_high t_low t_close t_timestamp <<< "${candles[$i]}"

    high_check=$(echo "$t_high $range_high" | awk '{if ($1 > $2) print 1; else print 0}')
    low_check=$(echo "$t_low $range_low" | awk '{if ($1 < $2) print 1; else print 0}')

    if [ "$high_check" = "1" ]; then
      range_high=$t_high
    fi
    if [ "$low_check" = "1" ]; then
      range_low=$t_low
    fi
  done

  last_candle="${candles[$((candle_count - 1))]}"
  IFS='|' read -r t_open t_high t_low t_close t_timestamp <<< "$last_candle"

  range_width=$(awk -v high="$range_high" -v low="$range_low" 'BEGIN {printf "%.2f", (high - low) / low * 100}')
  range_limit=$(awk -v threshold="$RANGE_THRESHOLD" 'BEGIN {printf "%.2f", threshold * 100}')
  is_sideways=$(awk -v width="$range_width" -v limit="$range_limit" 'BEGIN {if (width < limit) print 1; else print 0}')

  if [ "$is_sideways" = "1" ]; then
    breakout_up=$(awk -v high="$range_high" -v threshold="$BREAKOUT_THRESHOLD" 'BEGIN {printf "%.2f", high * (1 + threshold)}')
    breakout_down=$(awk -v low="$range_low" -v threshold="$BREAKOUT_THRESHOLD" 'BEGIN {printf "%.2f", low * (1 - threshold)}')

    breakout_up_check=$(awk -v last_close="$t_close" -v breakout="$breakout_up" 'BEGIN {if (last_close > breakout) print 1; else print 0}')
    if [ "$breakout_up_check" = "1" ]; then
      change=$(awk -v last_close="$t_close" -v high="$range_high" 'BEGIN {printf "%.2f", (last_close - high) / high * 100}')
      breakup_coins="${breakup_coins}${coin_id}(${symbol}), "
      breakup_details="${breakup_details}${coin_id} (${symbol})
  收盘价: \$${t_close}
  突破区间: \$${range_low} - \$${range_high}
  区间宽度: ${range_width}%
  突破幅度: +${change}%

"
    fi

    breakout_down_check=$(awk -v last_close="$t_close" -v breakout="$breakout_down" 'BEGIN {if (last_close < breakout) print 1; else print 0}')
    if [ "$breakout_down_check" = "1" ]; then
      change=$(awk -v last_close="$t_close" -v low="$range_low" 'BEGIN {printf "%.2f", (low - last_close) / low * 100}')
      breakdown_coins="${breakdown_coins}${coin_id}(${symbol}), "
      breakdown_details="${breakdown_details}${coin_id} (${symbol})
  收盘价: \$${t_close}
  突破区间: \$${range_low} - \$${range_high}
  区间宽度: ${range_width}%
  突破幅度: -${change}%

"
    fi
  fi

done

# 如果有突破，发送邮件
if [ -n "$breakup_coins" ] || [ -n "$breakdown_coins" ]; then
  email_subject="【币圈突破警报】$(date '+%Y/%m/%d %H:%M')"

  email_body="检测到K线突破！

检测时间: $(date '+%Y/%m/%d %H:%M')
扫描范围: 交易量前50币种
K线周期: 4小时
回溯K线数: ${LOOKBACK_CANDLES}根
震荡阈值: ${RANGE_THRESHOLD}%
突破阈值: ${BREAKOUT_THRESHOLD}%

"

  if [ -n "$breakup_coins" ]; then
    email_body="${email_body}
🚀 向上突破:
${breakup_coins%, }

详细:
${breakup_details}
"
  fi

  if [ -n "$breakdown_coins" ]; then
    email_body="${email_body}
💥 向下突破:
${breakdown_coins%, }

详细:
${breakdown_details}
"
  fi

  email_body="${email_body}
---
数据来源: CryptoCompare API"

  # 尝试发送邮件
  python3 /root/clawd/scripts/send_email.py "$email_subject" "$email_body" > /tmp/email_send.log 2>&1

  if [ $? -eq 0 ]; then
    echo "已发送突破警报到: $EMAIL_RECIPIENT"
    echo "向上突破: ${breakup_coins%, }"
    echo "向下突破: ${breakdown_coins%, }"
  else
    echo "邮件发送失败，详情见: /tmp/email_send.log"
  fi
else
  echo "未检测到突破，不发送邮件"
fi
