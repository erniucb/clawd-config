#!/bin/bash
# 停止守护进程

SCRIPT_DIR="/root/clawd/scripts"
WATCHDOG="$SCRIPT_DIR/watchdog-scanner.sh"

echo "=================================="
echo "🛑 停止守护进程"
echo "=================================="

# 查找守护进程
WATCHDOG_PID=$(ps aux | grep "$WATCHDOG" | grep -v grep | awk '{print $2}')

if [ -n "$WATCHDOG_PID" ]; then
    echo "📍 找到守护进程 (PID: $WATCHDOG_PID)"
    echo "🛑 正在停止..."

    kill $WATCHDOG_PID 2>/dev/null
    sleep 2

    # 如果还在运行，强制kill
    if ps -p $WATCHDOG_PID > /dev/null 2>&1; then
        echo "⚠️ 正常停止失败，强制终止..."
        kill -9 $WATCHDOG_PID 2>/dev/null
        sleep 1
    fi

    if ps -p $WATCHDOG_PID > /dev/null 2>&1; then
        echo "❌ 停止失败，进程仍在运行"
        exit 1
    else
        echo "✅ 守护进程已停止"
    fi
else
    echo "❌ 未找到运行中的守护进程"
fi

echo ""
echo "注意: 停止守护进程不会停止扫描器"
echo "如需停止扫描器，请运行: $SCRIPT_DIR/stop-survivor-scanner.sh"
