#!/bin/bash
# 检查和修复 clawdbot 配置问题

CONFIG_FILE="$HOME/.clawdbot/clawdbot.json"

echo "==================================="
echo "🔍 clawdbot 配置诊断"
echo "==================================="
echo ""

# 1. 检查当前模型配置
echo "📊 当前模型配置:"
echo ""
jq -r '.models.providers.myrelay' "$CONFIG_FILE" 2>/dev/null || echo "   (无法读取)"
echo ""

# 2. 测试官方API直连（绕过MyRelay）
echo "🌐 测试官方API直连..."

echo "   尝试连接 Zai 官方..."
curl -s -o /dev/null -w "%{http_code}" https://api.zhipuai.cn/v1/models
ZAI_CODE=$?

echo "   Zai 官方状态: $ZAI_CODE"
echo ""

# 3. 检查 MyRelay BaseURL 状态
echo "🔗 测试 MyRelay BaseURL..."
MYRELAY_URL=$(jq -r '.models.providers.myrelay.baseUrl' "$CONFIG_FILE" 2>/dev/null)

if [ -n "$MYRELAY_URL" ]; then
    echo "   当前配置: $MYRELAY_URL"
    
    # 提取IP和端口
    URL_IP=$(echo "$MYRELAY_URL" | sed -n 's|.*//\([^:]*\).*|\1|p')
    URL_PORT=$(echo "$MYRELAY_URL" | sed -n 's|.*:\([0-9]*\).*|\1|p')
    
    echo "   测试IP: $URL_IP"
    echo "   测试端口: $URL_PORT"
    
    # 尝试端口连接
    timeout 3 bash -c "cat < /dev/null > /dev/tcp/$URL_IP/$URL_PORT" 2>/dev/null
    PORT_STATUS=$?
    
    if [ $PORT_STATUS -eq 0 ]; then
        echo "   ✅ 端口可达"
        
        # 尝试HTTP请求
        curl -s -o /dev/null -w "%{http_code}" $MYRELAY_URL/v1/models
        HTTP_STATUS=$?
        
        if [ $HTTP_STATUS -eq 200 ]; then
            echo "   ✅ BaseURL工作正常 (HTTP 200)"
        elif [ $HTTP_STATUS -eq 401 ]; then
            echo "   ⚠️  BaseURL需要认证 (401)"
        elif [ $HTTP_STATUS -eq 403 ]; then
            echo "   ⚠️  BaseURL禁止访问 (403)"
        else
            echo "   ❌ BaseURL返回错误 (HTTP $HTTP_STATUS)"
        fi
    else
        echo "   ❌ 端口不可达 (BaseURL可能已失效)"
    fi
else
    echo "   (未找到MyRelay BaseURL配置)"
fi

echo ""
echo "==================================="
echo "💡 诊断建议"
echo "==================================="
echo ""

if [ "$ZAI_CODE" = "200" ]; then
    echo "✅ Zai官方API正常"
    echo ""
    echo "🔧 建议方案：切换到Zai官方API"
    echo ""
    echo "如果MyRelay转发失效，可以："
    echo "   1. 在clawdbot.json中修改模型配置"
    echo "   2. 将 primary model 改为: zai/glm-4.7"
    echo "   3. 删除或禁用 myrelay provider"
    echo ""
    echo "或者运行以下命令切换："
    echo "   clawdbot config set models.primary zai/glm-4.7"
else
    echo "⚠️  Zai官方API也异常 (HTTP $ZAI_CODE)"
    echo ""
    echo "可能原因："
    echo "   1. VPS IP被限制"
    echo "   2. API Key无效或过期"
    echo "   3. 网络问题"
fi

echo ""
echo "==================================="
