#!/bin/bash
# 查看守护进程和扫描器状态

SCRIPT_DIR="/root/clawd/scripts"
WATCHDOG="$SCRIPT_DIR/watchdog-scanner.sh"
WATCHDOG_LOG="$SCRIPT_DIR/watchdog.log"
SCANNER_PID_FILE="$SCRIPT_DIR/survivor-scanner.pid"

echo "=================================="
echo "📊 幸存者猎手状态检查"
echo "=================================="
echo ""

# 检查守护进程
echo "🛡️ 守护进程:"
if ps aux | grep -v grep | grep "$WATCHDOG" > /dev/null; then
    WATCHDOG_PID=$(ps aux | grep -v grep | grep "$WATCHDOG" | awk '{print $2}')
    WATCHDOG_UPTIME=$(ps -o etime= -p "$WATCHDOG_PID")
    echo "   ✅ 运行中"
    echo "   PID: $WATCHDOG_PID"
    echo "   运行时间: $WATCHDOG_UPTIME"
    echo ""
    echo "📋 最近10条监控日志:"
    tail -10 "$WATCHDOG_LOG" | sed 's/^/     /'
else
    echo "   ❌ 未运行"
    echo "   启动命令: $SCRIPT_DIR/start-watchdog.sh"
fi

echo ""
echo "🔍 扫描器:"
if [ -f "$SCANNER_PID_FILE" ]; then
    SCANNER_PID=$(cat "$SCANNER_PID_FILE")
    if ps -p $SCANNER_PID > /dev/null 2>&1; then
        SCANNER_UPTIME=$(ps -o etime= -p "$SCANNER_PID")
        SCANNER_MEM=$(ps -o rss= -p "$SCANNER_PID" | awk '{print int($1/1024)" "MB"}')
        echo "   ✅ 运行中"
        echo "   PID: $SCANNER_PID"
        echo "   运行时间: $SCANNER_UPTIME"
        echo "   内存占用: $SCANNER_MEM"
    else
        echo "   ❌ 未运行 (PID文件存在但进程不存在)"
        echo "   可能被watchdog自动停止了"
    fi
else
    echo "   ❌ 未运行"
    echo "   PID文件不存在"
fi

echo ""
echo "=================================="
echo "💡 管理命令"
echo "=================================="
echo "启动守护: $SCRIPT_DIR/start-watchdog.sh"
echo "停止守护: $SCRIPT_DIR/stop-watchdog.sh"
echo "查看状态: $SCRIPT_DIR/status-watchdog.sh"
echo ""
echo "手动管理扫描器:"
echo "  停止: $SCRIPT_DIR/stop-survivor-scanner.sh"
echo "  启动: $SCRIPT_DIR/start-survivor-scanner.sh"
echo "  查看日志: tail -f $SCRIPT_DIR/v20_run.log"
