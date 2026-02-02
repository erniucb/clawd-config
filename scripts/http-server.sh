#!/bin/bash
# 简易HTTP服务器 - 用于快速传输文件

PORT="${1:-8000}"
DIRECTORY="${2:-/root/clawd}"

cd "$DIRECTORY"

echo "📤 正在启动HTTP服务器..."
echo "端口: $PORT"
echo "目录: $DIRECTORY"
echo ""
echo "在浏览器访问: http://198.12.121.254:$PORT"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 使用Python 3的简单HTTP服务器
python3 -m http.server "$PORT"
