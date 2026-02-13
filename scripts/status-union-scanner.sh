#!/bin/bash
# 万物并集猎手 (异步版) 状态检查脚本

SCRIPT_DIR="/root/clawd/scripts"
PID_FILE="$SCRIPT_DIR/union-scanner.pid"
LOG_FILE="$SCRIPT_DIR/hunter_run.log"
DB_FILE="$SCRIPT_DIR/hunter_data.db"

echo "🔍 万物并集猎手状态检查"
echo "=================================="
echo "版本: V11.0 (Asyncio 并发超跑版)"
echo ""

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 运行中"
        echo "   PID: $PID"
        echo "   启动时间: $(ps -o lstart= -p $PID)"
    else
        echo "❌ 已停止 (PID文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
else
    echo "❌ 未运行"
fi

echo ""
echo "📊 数据库状态:"
if [ -f "$DB_FILE" ]; then
    WATCHLIST_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM watchlist" 2>/dev/null || echo "0")
    ALERT_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM alert_history" 2>/dev/null || echo "0")
    echo "   盯盘目标: $WATCHLIST_COUNT 个"
    echo "   历史记录: $ALERT_COUNT 条"
else
    echo "   (无数据库文件)"
fi

echo ""
echo "📋 最近20条日志:"
echo "----------------------------------"
if [ -f "$LOG_FILE" ]; then
    tail -20 "$LOG_FILE"
else
    echo " (暂无日志)"
fi
echo "----------------------------------"

echo ""
echo "常用命令:"
echo "   tail -f $LOG_FILE       # 实时日志"
echo "   sqlite3 $DB_FILE        # 查看数据库"
