#!/bin/bash
# 幸存者猎手启动脚本

SCRIPT_DIR="/root/clawd/scripts"
PYTHON_SCRIPT="$SCRIPT_DIR/survivor-scanner.py"
PID_FILE="$SCRIPT_DIR/survivor-scanner.pid"
LOG_FILE="$SCRIPT_DIR/survivor_run.log"

cd "$SCRIPT_DIR"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ 幸存者猎手已经在运行中 (PID: $PID)"
        echo "如需重启，请先运行: $SCRIPT_DIR/stop-survivor-scanner.sh"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动扫描器
echo "🚀 启动幸存者猎手 V13.0..."
nohup python3 "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

echo "✅ 幸存者猎手已启动!"
echo "   版本: V13.0 (OKX/MEXC/BITGET/GATE)"
echo "   PID: $(cat $PID_FILE)"
echo "   日志: $LOG_FILE"
echo ""
echo "查看日志:"
echo "   tail -f $LOG_FILE"
echo ""
echo "查看状态:"
echo "   $SCRIPT_DIR/status-survivor-scanner.sh"
