#!/bin/bash
# 小龙虾1号每日选题推送脚本
# 由cron定时触发

PROJECT_DIR="/root/clawd/projects/xiaolongxia-ai"
LOG_FILE="/root/clawd/scripts/xiaolongxia_daily.log"

echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始每日选题扫描" >> "$LOG_FILE"

# 运行研究Agent
cd "$PROJECT_DIR"
python3 research_agent.py >> "$LOG_FILE" 2>&1

# 检查是否成功生成选题
TOPICS_FILE="$PROJECT_DIR/data/hot_topics.json"
if [ -f "$TOPICS_FILE" ]; then
    echo "✅ 选题生成成功" >> "$LOG_FILE"
    # 这里可以添加推送逻辑
    # OpenClaw会通过cron的message字段推送
else
    echo "❌ 选题生成失败" >> "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 选题扫描完成" >> "$LOG_FILE"
