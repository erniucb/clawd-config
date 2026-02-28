#!/bin/bash

# BTC 价格监控脚本
# 如果价格低于 64730，发送飞书提醒

THRESHOLD=64730
LOG_FILE="/root/clawd/scripts/btc_monitor.log"
USER_ID="ou_e47763504a4684b5004e3654e555249b"

# 获取当前 BTC 价格
PRICE=$(python3 -c "
import ccxt
okx = ccxt.okx()
ticker = okx.fetch_ticker('BTC/USDT')
print(ticker['last'])
" 2>/dev/null)

if [ -z "$PRICE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 获取价格失败" >> "$LOG_FILE"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 当前 BTC 价格: \$${PRICE}" >> "$LOG_FILE"

# 比较价格
if (( $(echo "$PRICE < $THRESHOLD" | bc -l) )); then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ⚠️ 警报！价格低于 $THRESHOLD！" >> "$LOG_FILE"
    
    # 使用 OpenClaw 发送消息
    curl -s -X POST "http://127.0.0.1:18789/api/message" \
        -H "Authorization: Bearer b1d65fd8cf60188a3c66c7440380fd1b1f9d980c3d1611d8" \
        -H "Content-Type: application/json" \
        -d "{
            \"channel\": \"feishu\",
            \"target\": \"user:${USER_ID}\",
            \"message\": \"⚠️ BTC 价格警报！\\n\\n当前价格: \$${PRICE}\\n目标价格: \$${THRESHOLD}\\n\\n价格已跌破目标位！\"
        }" >> "$LOG_FILE" 2>&1
fi
