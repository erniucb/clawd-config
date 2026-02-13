#!/bin/bash
# 幸存者猎手守护进程 - 自动监控和重启

SCRIPT_DIR="/root/clawd/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/survivor-scanner.py"
PID_FILE="$SCRIPT_DIR/survivor-scanner.pid"
MONITOR_LOG="$SCRIPT_DIR/watchdog.log"
CHECK_INTERVAL=60  # 检查间隔（秒）

# 创建日志目录
mkdir -p "$SCRIPT_DIR"

echo "=================================="
echo "🛡️ 幸存者猎手守护进程启动"
echo "=================================="
echo "监控脚本: $PYTHON_SCRIPT"
echo "PID文件: $PID_FILE"
echo "检查间隔: ${CHECK_INTERVAL}秒"
echo "监控日志: $MONITOR_LOG"
echo ""

# 记录日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

# 检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# 启动脚本
start_scanner() {
    log "🚀 检测到脚本未运行，启动中..."
    cd "$SCRIPT_DIR"

    # 使用后台模式启动
    nohup python3 "$PYTHON_SCRIPT" >> "$SCRIPT_DIR/survivor_run.log" 2>&1 &

    # 保存新的PID
    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"

    # 等待2秒确认启动
    sleep 2

    if ps -p $NEW_PID > /dev/null 2>&1; then
        log "✅ 成功启动 (PID: $NEW_PID)"
    else
        log "❌ 启动失败"
        return 1
    fi

    return 0
}

# 获取脚本状态
get_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        UPTIME=$(ps -o etime= -p "$PID")
        MEM=$(ps -o rss= -p "$PID" | awk '{print int($1/1024)" "MB"}')
        echo "✅ 运行中"
        echo "   PID: $PID"
        echo "   运行时间: $UPTIME"
        echo "   内存占用: $MEM MB"
    else
        echo "❌ 未运行"
    fi
}

# 主监控循环
log "🔍 开始守护监控..."

LOOP_COUNT=0
while true; do
    ((LOOP_COUNT++))

    # 记录检查
    log "🔍 [第${LOOP_COUNT}次检查] 检测进程状态..."

    if is_running; then
        log "✅ 进程正常运行"
        # 每12小时显示一次状态
        if [ $((LOOP_COUNT % 720)) -eq 0 ]; then
            log "📊 定期状态报告:"
            get_status
        fi
    else
        log "❌ 检测到进程异常，尝试重启..."
        start_scanner
        if [ $? -eq 0 ]; then
            log "✅ 重启成功，继续监控..."
        else
            log "❌ 重启失败，等待下次检查..."
        fi
    fi

    # 等待下次检查
    sleep "$CHECK_INTERVAL"
done
