#!/bin/bash

# DuckDuckGo搜索脚本（HTML版本）
# 免费使用，无需API密钥

QUERY="$1"
MAX_RESULTS="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 '搜索关键词' [结果数量]"
    exit 1
fi

echo "搜索: $QUERY"
echo "---"

# 使用DuckDuckGo搜索结果页面
URL="https://duckduckgo.com/html/?q=$(echo $QUERY | sed 's/ /+/g')"

# 获取搜索结果
curl -s "$URL" | \
    grep -A 2 'class="result__a"' | \
    grep -E '(result__a|result__url|result__snippet)' | \
    sed 's/<[^>]*>//g' | \
    sed 's/&amp;/\&/g' | \
    awk -v max=$MAX_RESULTS '
    BEGIN { count = 0 }
    /https?:\/\// {
        if (count < max) {
            count++
            print count ". " $0
        }
    }
    '
