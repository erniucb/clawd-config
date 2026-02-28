#!/bin/bash
# Crypto & AI 热门内容 + 融资推送
# 每小时9-23点执行（UTC+8）

# 加载环境变量
source /root/.bashrc

# 6551 API Token
TOKEN="$TWITTER_TOKEN"

# Telegram Chat ID
CHAT_ID="1673887193"

# 当前时间（UTC+8）
HOUR=$(TZ='Asia/Shanghai' date +%H)
DATE=$(TZ='Asia/Shanghai' date '+%Y-%m-%d')
TODAY=$(TZ='Asia/Shanghai' date '+%Y-%m-%d')

# 缓存文件
CACHE_DIR="/root/clawd/cache"
mkdir -p "$CACHE_DIR"
FUNDING_CACHE="$CACHE_DIR/funding-$TODAY.json"

# 检查时间范围
if [ "$HOUR" -lt 9 ] || [ "$HOUR" -gt 23 ]; then
    echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')] 跳过（不在9-23点）"
    exit 0
fi

echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')] 开始搜索..."

# 构建消息
MSG="🔥 **Crypto & AI 热门推送** ($DATE $HOUR:00)\n\n"

# ============================================
# 1. RootData 融资信息（用playwright抓取）
# ============================================
echo "  抓取 RootData 融资信息..."

# 用mcporter调用playwright抓取
FUNDING_DATA=$(mcporter call playwright navigate --url "https://cn.rootdata.com/Fundraising" 2>/dev/null)

# 简化方案：用6551的news_search搜索融资新闻
FUNDING_NEWS=$(curl -s -X POST "https://ai.6551.io/open/news_search" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"q": "融资 Web3 crypto funding", "limit": 5, "page": 1}' 2>/dev/null)

# 提取今天的融资新闻
FUNDING_ITEMS=$(echo "$FUNDING_NEWS" | jq -r --arg today "$TODAY" '
    .data[]? | 
    select(.publishedTime // "" | contains($today)) |
    "• \(.text // "" | .[0:80])...\n  💰 \(.link // "")"
' 2>/dev/null | head -3)

if [ -n "$FUNDING_ITEMS" ]; then
    MSG+="💰 **今日融资**:\n$FUNDING_ITEMS\n\n"
fi

# ============================================
# 2. Twitter热门
# ============================================
echo "  搜索 Twitter..."

search_twitter() {
    local q="$1"
    curl -s -X POST "https://ai.6551.io/open/twitter_search" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"keywords\": \"$q\", \"maxResults\": 3, \"product\": \"Top\"}" 2>/dev/null | \
        jq -r '.data[]? | "• [\(.userScreenName // "unknown")] \(.text // "" | .[0:80])...\n  ❤️\(.favoriteCount // 0)"' 2>/dev/null
}

KEYWORDS=("Polymarket" "预测市场" "空投" "openclaw")

TWITTER_RESULTS=""
for kw in "${KEYWORDS[@]}"; do
    result=$(search_twitter "$kw")
    if [ -n "$result" ]; then
        TWITTER_RESULTS+="$result\n\n"
        break
    fi
    sleep 0.2
done

if [ -n "$TWITTER_RESULTS" ]; then
    MSG+="🐦 **Twitter**:\n$TWITTER_RESULTS"
fi

# ============================================
# 3. News热门
# ============================================
echo "  搜索 News..."

search_news() {
    local q="$1"
    curl -s -X POST "https://ai.6551.io/open/news_search" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"q\": \"$q\", \"limit\": 3, \"page\": 1}" 2>/dev/null | \
        jq -r '.data[]? | "• \(.text // "" | .[0:80])...\n  📊 AI: \(.aiRating.score // "N/A")"' 2>/dev/null
}

NEWS_RESULTS=""
for kw in "${KEYWORDS[@]}"; do
    result=$(search_news "$kw")
    if [ -n "$result" ]; then
        NEWS_RESULTS+="$result\n\n"
        break
    fi
    sleep 0.2
done

if [ -n "$NEWS_RESULTS" ]; then
    MSG+="📰 **新闻**:\n$NEWS_RESULTS"
fi

# ============================================
# 如果没有任何结果
# ============================================
if [ -z "$FUNDING_ITEMS" ] && [ -z "$TWITTER_RESULTS" ] && [ -z "$NEWS_RESULTS" ]; then
    MSG+="😔 本次未找到相关内容\n\n"
fi

MSG+="---\n⏰ 下次推送: 1小时后"

# ============================================
# 推送到Telegram
# ============================================
echo "  推送到Telegram..."
echo -e "$MSG" > /tmp/crypto-push.txt

if openclaw message send --channel telegram --target "$CHAT_ID" --message "$(cat /tmp/crypto-push.txt)" --json > /tmp/push-response.json 2>&1; then
    echo "✅ 推送成功"
else
    echo "❌ 推送失败"
    cat /tmp/push-response.json
fi

rm -f /tmp/crypto-push.txt /tmp/push-response.json

echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M')] 完成"
