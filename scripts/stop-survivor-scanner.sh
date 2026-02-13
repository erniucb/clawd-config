#!/bin/bash
# 幸存者猎手停止脚本

SCRIPT_DIR="/root/clawd/scripts"
PID_FILE="$SCRIPT_DIR/survivor-scanner.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "❌ 没有找到运行中的幸存者猎手"
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "🛑 正在停止幸存者猎手 (PID: $PID)..."
    kill $PID
    sleep 2

    # 如果还在运行，强制kill
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  正常停止失败，强制终止..."
        kill -9 $PID
    fi

    rm -f "$PID_FILE"
    echo "✅ 幸存者猎手已停止"
else
    echo "⚠️  进程不存在，清理PID文件"
    rm -f "$PID_FILE"
fi
