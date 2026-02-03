#!/bin/bash
# 小红书幼教头部账号监控脚本
# 功能：每6小时检查对标账号最近24小时笔记，检测共同主题

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/xiaohongshu"
LOG_FILE="$DATA_DIR/monitor.log"

# 创建数据目录
mkdir -p "$DATA_DIR"

# 监控账号列表
ACCOUNTS=(
  "幼师打工人:2697397947"
  "小鹿老师幼儿园教育咨询:94105668276"
  "一小只晨晨咨询:26965256048"
)

# 记录日志
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 提取关键词（简单版本：提取2-3字的关键词）
extract_keywords() {
  local title="$1"
  # 常见幼教主题关键词
  local keywords="家长会|元宵节|春分|清明节|劳动节|儿童节|端午节|中秋节|国庆节|圣诞节|春节|端午节|母亲节|父亲节|开学|期末|毕业|亲子活动|手工|绘画|游戏|故事|儿歌|数学|英语|阅读|习惯养成|自理能力|社交|情绪管理|安全|健康|营养"

  echo "$title" | grep -oE "$keywords" | sort -u
}

# 主监控逻辑
main() {
  log "=== 开始监控检查 ==="

  local all_keywords=()
  local keyword_count=()

  # 收集所有账号的关键词
  for account in "${ACCOUNTS[@]}"; do
    local name="${account%%:*}"
    local id="${account##*:}"
    local account_file="$DATA_DIR/${id}_latest.txt"

    log "检查账号: $name (ID: $id)"

    # TODO: 这里需要实际调用小红书API或使用浏览器自动化获取笔记
    # 暂时使用示例数据
    if [ -f "$account_file" ]; then
      log "读取已有数据: $account_file"
      while read -r title; do
        local kws=$(extract_keywords "$title")
        for kw in $kws; do
          all_keywords+=("$kw:$name")
        done
      done < "$account_file"
    else
      log "数据文件不存在，创建占位文件"
      echo "占位数据 - 需要实际抓取" > "$account_file"
    fi
  done

  # 统计关键词出现次数
  declare -A kw_accounts
  for item in "${all_keywords[@]}"; do
    local kw="${item%%:*}"
    local acc="${item##*:}"
    kw_accounts["$kw"]="${kw_accounts[$kw]} $acc"
  done

  # 检测共同主题（3个账号都发了）
  local alerts=()
  for kw in "${!kw_accounts[@]}"; do
    local accounts="${kw_accounts[$kw]}"
    local count=$(echo "$accounts" | wc -w)

    if [ "$count" -ge 3 ]; then
      log "🚨 检测到共同主题: $kw (账号: $accounts)"
      alerts+=("主题: $kw - 账号: $accounts")
    fi
  done

  # 发送警报
  if [ ${#alerts[@]} -gt 0 ]; then
    log "发送警报通知"
    for alert in "${alerts[@]}"; do
      # TODO: 通过Clawdbot消息系统发送
      echo "需要发送警报: $alert" >> "$DATA_DIR/alerts.txt"
    done
  fi

  log "=== 监控检查完成 ==="
}

main "$@"
