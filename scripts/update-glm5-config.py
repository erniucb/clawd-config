#!/usr/bin/env python3
import json

CONFIG_FILE = "/root/.clawdbot/clawdbot.json"

# 新的GLM-5配置
NEW_CONFIG = {
    "baseUrl": "https://open.bigmodel.cn/api/anthropic",
    "apiKey": "21ec9675278447b98fe205f249d598d9.V7mUtuA0vgaAnqSO",
    "api": "anthropic",
    "models": []
}

# 读取配置
with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

# 1. 删除myrelay provider
if "myrelay" in config["models"]["providers"]:
    del config["models"]["providers"]["myrelay"]
    print("✅ 已删除 myrelay provider")

# 2. 添加zhipu provider
config["models"]["providers"]["zhipu"] = NEW_CONFIG
print("✅ 已添加 zhipu provider")

# 3. 更新primary model
config["models"]["primary"] = "zhipu/glm-4"
print("✅ 已设置 primary model: zhipu/glm-4")

# 4. 更新zhipu的fallbacks
if "fallbacks" in config["models"]:
    config["models"]["fallbacks"] = ["zhipu/glm-4"]
    print("✅ 已更新 fallbacks")
else:
    config["models"]["fallbacks"] = ["zhipu/glm-4"]
    print("✅ 已设置 fallbacks")

# 写入配置
with open(CONFIG_FILE, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("\n==================================")
print("✅ 配置文件已更新")
print("==================================")
print("📊 新配置:")
print(f"   Provider: zhipu (智谱官方)")
print(f"   BaseURL: {NEW_CONFIG['baseUrl']}")
print(f"   Model: glm-4")
print(f"   Primary: zhipu/glm-4")
print("\n🔄 现在重启 gateway...")
print("==================================")
