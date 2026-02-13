#!/bin/bash
# 重启扫描器 (不停止watchdog)

SCRIPT_DIR="/root/clawd/scripts"
SCANNER_PID_FILE="$SCRIPT_DIR/survivor-scanner.pid"

echo "=================================="
echo "🔄 重启幸存者猎手扫描器"
echo "=================================="
echo ""

# 停止旧的扫描器进程
if [ -f "$SCANNER_PID_FILE" ]; then
    OLD_PID=$(cat "$SCANNER_PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 停止旧扫描器进程 (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2

        # 如果还在运行，强制kill
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "⚠️  正常停止失败，强制终止..."
            kill -9 $OLD_PID
            sleep 1
        fi

        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "❌ 停止失败，进程仍在运行"
            exit 1
        else
            echo "✅ 旧扫描器已停止"
        fi
    else
        echo "ℹ️  PID文件存在但进程不存在"
    fi
else
    echo "ℹ️  未找到PID文件"
fi

# 启动新的扫描器
echo ""
echo "🚀 启动新的扫描器..."
cd "$SCRIPT_DIR"
nohup python3 survivor-scanner.py >> v20_run.log 2>&1 &

# 保存新的PID
NEW_PID=$!
echo "$NEW_PID" > "$SCANNER_PID_FILE"

# 确认启动
sleep 2
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "✅ 扫描器重启成功!"
    echo "   新PID: $NEW_PID"
    echo "   日志: $SCRIPT_DIR/v20_run.log"
    echo ""
    echo "📊 注意:"
    echo "   - watchdog会自动监控扫描器状态"
    echo "   - 如果扫描器挂掉，watchdog会自动重启"
    echo "   - 查看状态: $SCRIPT_DIR/status-watchdog.sh"
else
    echo "❌ 扫描器启动失败!"
    exit 1
fi
