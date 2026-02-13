#!/bin/bash
# 万物并集猎手 (异步版) 启动脚本

SCRIPT_DIR="/root/clawd/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/union-scanner.py"
PID_FILE="$SCRIPT_DIR/union-scanner.pid"
LOG_FILE="$SCRIPT_DIR/hunter_run.log"

cd "$SCRIPT_DIR"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ 万物并集猎手已经在运行中 (PID: $PID)"
        echo "如需重启，请先运行: $SCRIPT_DIR/stop-union-scanner.sh"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动扫描器
echo "🚀 启动万物并集猎手 (Asyncio 并发超跑版)..."
nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

echo "✅ 万物并集猎手已启动!"
echo "   版本: V11.0 (Asyncio 并发超跑版)"
echo "   PID: $(cat $PID_FILE)"
echo "   日志: $LOG_FILE"
echo ""
echo "查看日志:"
echo "   tail -f $LOG_FILE"
echo ""
echo "停止扫描器:"
echo "   $SCRIPT_DIR/stop-union-scanner.sh"
echo ""
echo "查看状态:"
echo "   $SCRIPT_DIR/status-union-scanner.sh"
