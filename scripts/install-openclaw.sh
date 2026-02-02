#!/bin/bash
# OpenClaw 安装脚本（使用npx）

echo "正在下载 OpenClaw CLI..."
npm install -g @clawdhub/cli 2>&1 | tail -5

echo ""
echo "测试安装..."
npx clawdhub --version 2>&1

echo ""
if [ $? -eq 0 ]; then
    echo "✅ OpenClaw CLI 安装成功！"
    echo ""
    echo "使用方法："
    echo "  npx clawdhub search <keyword>     - 搜索技能"
    echo "  npx clawdhub install <skill>     - 安装技能"
    echo "  npx clawdhub list                - 列出技能"
else
    echo "❌ 安装失败，请检查npm配置"
fi
