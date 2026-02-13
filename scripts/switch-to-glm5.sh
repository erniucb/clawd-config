#!/bin/bash
# 一键切换到GLM-5官方API

echo "==================================="
echo "🚀 切换到 GLM-5 官方API"
echo "==================================="
echo ""

# 官方配置
NEW_BASE_URL="https://open.bigmodel.cn/api/anthropic"
NEW_API_KEY="21ec9675278447b98fe205f249d598d9.V7mUtuA0vgaAnqSO"
NEW_MODEL="glm-4"  # 或者 glm-4-flash, 根据官方支持

# 1. 添加zhipu provider
echo "📡 添加zhipu provider..."
clawdbot config set models.providers.zhipu.baseUrl "$NEW_BASE_URL"
clawdbot config set models.providers.zhipu.apiKey "$NEW_API_KEY"
clawdbot config set models.providers.zhipu.models '[]'  # 清空默认模型列表

# 2. 设置primary model
echo "🎯 设置primary model为GLM-5..."
clawdbot config set models.primary "zhipu/$NEW_MODEL"

# 3. 清除或禁用myrelay (避免冲突)
echo "🗑️ 清除myrelay配置..."
clawdbot config remove models.providers.myrelay
# 或者
# clawdbot config set models.providers.myrelay.baseUrl ""

# 4. 重启gateway应用新配置
echo "🔄 重启gateway..."
clawdbot gateway restart

echo ""
echo "==================================="
echo "✅ 配置完成！"
echo "==================================="
echo ""
echo "📊 新配置:"
echo "   Provider: zhipu (智谱官方)"
echo "   BaseURL: $NEW_BASE_URL"
echo "   Model: $NEW_MODEL"
echo "   API Key: ${NEW_API_KEY:0:20}...${NEW_API_KEY: -4}"
echo ""
echo "📋 查看配置:"
echo "   clawdbot config list"
echo ""
echo "🧪 测试连接:"
echo "   clawdbot config set models.primary zhipu/$NEW_MODEL"
echo "   然后在Control UI中发送测试消息"
echo ""
