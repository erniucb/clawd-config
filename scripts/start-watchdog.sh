#!/bin/bash
# 启动守护进程

SCRIPT_DIR="/root/clawd/scripts"
WATCHDOG="$SCRIPT_DIR/watchdog-scanner.sh"

echo "=================================="
echo "🛡️ 启动守护进程"
echo "=================================="

# 检查是否已经在运行
if ps aux | grep -v grep | grep "$WATCHDOG" > /dev/null; then
    echo "❌ 守护进程已经在运行中"
    echo "如需重启，请先运行: $SCRIPT_DIR/stop-watchdog.sh"
    exit 1
fi

# 启动守护进程
nohup "$WATCHDOG" > /dev/null 2>&1 &

echo "✅ 守护进程已启动!"
echo ""
echo "查看日志:"
echo "   tail -f $SCRIPT_DIR/watchdog.log"
echo ""
echo "查看状态:"
echo "   $SCRIPT_DIR/status-watchdog.sh"
echo ""
echo "停止守护进程:"
echo "   $SCRIPT_DIR/stop-watchdog.sh"
