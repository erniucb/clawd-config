#!/bin/bash

# DuckDuckGo搜索脚本
# 免费使用，无需API密钥

QUERY="$1"
MAX_RESULTS="${2:-5}"

if [ -z "$QUERY" ]; then
    echo "用法: $0 '搜索关键词' [结果数量]"
    exit 1
fi

echo "搜索: $QUERY"
echo "---"

# 使用DuckDuckGo Instant Answer API
curl -s "https://api.duckduckgo.com/?q=${QUERY}&format=json&no_html=1&skip_disambig=0" | \
    python3 -c "
import sys, json, urllib.parse
data = json.load(sys.stdin)

# 显示即时答案
if data.get('Abstract'):
    print('📌 即时答案:')
    print(f'{data[\"Abstract\"]}\n')

if data.get('Heading'):
    print('📌 标题:', data['Heading'])
    if data.get('Answer'):
        print('答案:', data['Answer'])
    print()

# 显示相关主题（如果有）
if data.get('RelatedTopics'):
    print('🔗 相关结果:')
    count = 0
    for topic in data['RelatedTopics']:
        if isinstance(topic, dict) and 'Text' in topic and 'FirstURL' in topic:
            count += 1
            if count > MAX_RESULTS:
                break
            text = topic['Text'].split(' - ')[0][:80]
            url = topic['FirstURL']
            print(f'{count}. {text}')
            print(f'   {url}\n')
elif data.get('Results'):
    print('🔗 搜索结果:')
    for i, result in enumerate(data['Results'][:MAX_RESULTS], 1):
        print(f'{i}. {result.get(\"Text\", \"无标题\")}')
        print(f'   {result.get(\"FirstURL\", \"无链接\")}\n')
" 2>/dev/null || echo "搜索失败"
