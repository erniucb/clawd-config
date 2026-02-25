# 小红书自动化系统使用说明

## 📱 功能概述

本系统提供小红书自动化功能：
- ✅ 每日定时搜索热门笔记
- ✅ 自动收集和保存搜索结果
- ✅ 支持发布笔记（需要登录）
- ✅ 检查登录状态

## 🔧 当前状态

### 已安装组件
- ✅ `@fastmcp-me/xhs-mcp` - 小红书 CLI 工具
- ✅ `xhs-automation.py` - 自动化脚本
- ✅ 定时任务配置文件

### 当前限制
- ⚠️ **未登录小红书**：搜索功能受限，无法发布笔记
- ⚠️ 服务器无图形界面：无法直接使用 `npx login` 命令

## 🚀 如何启用完整功能

### 方案1：使用 Cookies（推荐）

1. **在你的本地电脑上登录小红书**
   - 访问 https://www.xiaohongshu.com
   - 使用浏览器正常登录

2. **安装 Cookie-Editor 扩展**
   - Chrome: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
   - Firefox: https://addons.mozilla.org/firefox/addon/cookie-editor/

3. **导出小红书 Cookies**
   - 打开小红书网站
   - 点击 Cookie-Editor 扩展
   - 点击 "Export" → 选择 "Header String" 格式
   - 复制整个 cookie 字符串

4. **发送给小桃**
   - 将 cookie 字符串发送给小桃
   - 小桃会帮你配置到系统中

### 方案2：使用小红书开发者 API

- 申请小红书开放平台开发者权限
- 获取 API Key 和 Secret
- 配置到系统中

## 📋 当前可用命令

### 手动执行搜索
```bash
python3 /root/clawd/scripts/xhs-automation.py
```

### 检查登录状态
```bash
npx -y @fastmcp-me/xhs-mcp status
```

### 搜索笔记（未登录可能受限）
```bash
npx -y @fastmcp-me/xhs-mcp search "关键词"
```

### 查看搜索结果
```bash
cat /root/clawd/scripts/xhs_results/search_*.json
```

### 查看自动化日志
```bash
tail -f /root/clawd/scripts/xhs_automation.log
```

## ⏰ 定时任务配置

### 当前配置
- **上午搜索**: 每天 9:00（东八区）
- **下午搜索**: 每天 18:00（东八区）

### 修改搜索关键词
编辑 `/root/clawd/scripts/xhs-automation.py`，修改 `keywords` 列表：

```python
keywords = [
    "AI助手",
    "Web3",
    "加密货币",
    "技术分享",
    "OpenClaw",
    # 添加更多关键词...
]
```

### 添加/修改定时任务
编辑 `/root/clawd/scripts/xhs-cron.json`，然后让小桃帮你配置到系统。

## 📝 发布笔记功能（需要登录）

登录后，可以使用以下功能：

### Python 脚本方式
```python
from xhs_automation import XiaohongshuAutomation

automation = XiaohongshuAutomation()

# 发布笔记
success = automation.publish_note(
    title="笔记标题",
    content="笔记内容...",
    image_paths=["/path/to/image1.jpg", "/path/to/image2.jpg"]
)
```

### 命令行方式
```bash
npx -y @fastmcp-me/xhs-mcp publish \
  --title "笔记标题" \
  --content "笔记内容" \
  --images "image1.jpg,image2.jpg"
```

## 📊 结果存储

搜索结果会保存在：
```
/root/clawd/scripts/xhs_results/
├── search_20260225_002616.json
├── search_20260226_090000.json
└── ...
```

每个 JSON 文件包含：
- 搜索时间
- 每个关键词的搜索结果
- 笔记详情

## 🔍 故障排查

### 搜索结果为空
- 可能是未登录导致访问受限
- 检查登录状态：`npx -y @fastmcp-me/xhs-mcp status`
- 按照方案1配置 cookies

### 登录失败
- 服务器无图形界面，无法直接登录
- 必须使用 cookies 方案

### 定时任务不执行
- 检查日志：`tail -f /root/clawd/scripts/xhs_automation.log`
- 确认脚本权限：`ls -la /root/clawd/scripts/xhs-automation.py`
- 手动测试：`python3 /root/clawd/scripts/xhs-automation.py`

## 📞 需要帮助？

如果有任何问题，告诉小桃：
- "查看小红书自动化日志"
- "检查小红书登录状态"
- "修改搜索关键词"
- "添加新的定时任务"

## 🎯 下一步

1. **配置小红书登录**：按照方案1获取 cookies
2. **测试搜索功能**：手动运行一次脚本
3. **确认定时任务**：让小桃配置系统定时任务
4. **开始自动化**：享受每日自动搜索！

---

**创建时间**: 2026-02-25
**版本**: 1.0
**维护者**: 小桃 🍑
