#!/bin/bash

# Google搜索脚本
# 使用Google Custom Search API

API_KEY="AIzaSyAyu6QfoNhjYXv_8AinPxFl1IuXfWoLBvA"
# 使用Google的默认搜索引擎ID（搜索全网）
CX_ID="017576662512468239146:omuauf_lfve"

QUERY="$1"
MAX_RESULTS="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 '搜索关键词' [结果数量]"
    exit 1
fi

echo "搜索: $QUERY"
echo "---"

curl -s "https://www.googleapis.com/customsearch/v1?key=${API_KEY}&cx=${CX_ID}&q=${QUERY}&num=${MAX_RESULTS}" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'items' in data:
    for i, item in enumerate(data['items'], 1):
        title = item.get('title', '无标题')
        link = item.get('link', '无链接')
        snippet = item.get('snippet', '无描述')[:100]
        print(f'{i}. {title}')
        print(f'   {snippet}...')
        print(f'   {link}\n')
else:
    print('未找到搜索结果')
    if 'error' in data:
        print(f'错误: {data[\"error\"][\"message\"]}')
" 2>/dev/null || echo "解析失败，请检查API配置"
