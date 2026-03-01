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
    
    # 使用 OpenClaw CLI 发送消息
    openclaw message send \
        --channel feishu \
        --target "user:${USER_ID}" \
        --message "⚠️ BTC 价格警报！

当前价格: \$${PRICE}
目标价格: \$${THRESHOLD}

价格已跌破目标位！" >> "$LOG_FILE" 2>&1

    echo "$(date '+%Y-%m-%d %H:%M:%S') - 消息发送完成" >> "$LOG_FILE"
fi
