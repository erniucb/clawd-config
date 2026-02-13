#!/bin/bash
# 结构猎手状态检查脚本

SCRIPT_DIR="/root/clawd/scripts"
PID_FILE="$SCRIPT_DIR/structure-scanner.pid"
LOG_FILE="$SCRIPT_DIR/structure-scanner.log"

echo "🔍 结构猎手状态检查"
echo "=================================="

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 运行中"
        echo "   PID: $PID"
        echo ""
        echo "📊 最近10条日志:"
        echo "----------------------------------"
        tail -10 "$LOG_FILE"
        echo "----------------------------------"
    else
        echo "❌ 已停止 (PID文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
else
    echo "❌ 未运行"
fi

echo ""
echo "完整日志:"
echo "   tail -f $LOG_FILE"
