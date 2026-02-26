# OpenClaw Windows 安装指南

> 🦞 在 Windows 本地运行 OpenClaw，获得完整的浏览器自动化能力

## 📋 系统要求

- **操作系统**: Windows 10/11
- **Node.js**: v18+ 或 v20+（推荐 v20 LTS）
- **内存**: 至少 4GB（8GB 推荐）
- **浏览器**: Chrome 或 Edge（已安装）

---

## 🚀 安装步骤

### 1️⃣ 安装 Node.js

**方式 A：官网下载（推荐新手）**
1. 访问 https://nodejs.org/
2. 下载 **20.x LTS** 版本
3. 双击安装，一路下一步
4. 打开 PowerShell 验证：
   ```powershell
   node --version
   npm --version
   ```

**方式 B：使用 winget（推荐）**
```powershell
winget install OpenJS.NodeJS.LTS
```

**方式 C：使用 Chocolatey**
```powershell
choco install nodejs-lts
```

---

### 2️⃣ 安装 OpenClaw

**全局安装（推荐）**
```powershell
npm install -g openclaw
```

**验证安装**
```powershell
openclaw --version
openclaw status
```

---

### 3️⃣ 配置 OpenClaw

**首次运行**
```powershell
# 初始化配置
openclaw init

# 配置 AI 模型（必须）
openclaw configure --section ai
# 然后输入你的 API Key（OpenAI/Anthropic 等）
```

**配置文件位置**
- 配置文件: `~\.openclaw\openclaw.json`
- 工作目录: `~\clawd\`（默认）

---

### 4️⃣ 启动 Gateway（后台服务）

```powershell
# 启动 Gateway
openclaw gateway start

# 检查状态
openclaw gateway status

# 重启（如需要）
openclaw gateway restart
```

**提示**: Gateway 是后台服务，负责管理浏览器、消息通道等。建议设置开机自启：

```powershell
# 设置为 Windows 服务（可选）
openclaw gateway install-service
```

---

## 🌐 浏览器配置

### 方式 1：独立浏览器（OpenClaw 自带）

**启动浏览器**
```powershell
# 在聊天中让 AI 执行：
browser start profile=openclaw
```

**特点**：
- 独立的用户数据目录
- 不会干扰你的日常浏览器
- 适合自动化任务

---

### 方式 2：连接现有 Chrome（推荐）⭐

**步骤**：

1. **安装 OpenClaw Chrome 扩展**
   - Chrome 应用商店搜索 "OpenClaw"
   - 或访问：https://chrome.google.com/webstore （待上架）
   - 临时方案：手动加载扩展（见下方）

2. **在浏览器中附加标签页**
   - 打开 Chrome，访问任意网页
   - 点击 OpenClaw 扩展图标（工具栏右侧）
   - 扩展会显示 "✅ Attached"（已连接）

3. **让 AI 操作你的浏览器**
   ```
   你：打开浏览器访问淘宝，搜索机械键盘
   AI：browser open profile=chrome url="https://taobao.com"
   ```

**手动加载扩展（如果商店没上架）**：
1. 下载扩展源码：`git clone https://github.com/openclaw/openclaw`
2. Chrome 地址栏输入：`chrome://extensions/`
3. 右上角开启 "开发者模式"
4. 点击 "加载已解压的扩展程序"
5. 选择 `openclaw/extension` 目录

---

### 方式 3：使用 Edge

Edge 与 Chrome 共享 Chromium 内核，配置方法相同：
```powershell
browser start profile=openclaw browser=edge
```

---

## 📱 消息通道配置（可选）

### Telegram 配置

```powershell
# 配置 Telegram Bot
openclaw configure --section telegram

# 按提示输入：
# - Bot Token（从 @BotFather 获取）
# - Chat ID（你的用户 ID）
```

### 其他通道
- **Discord**: `openclaw configure --section discord`
- **Signal**: `openclaw configure --section signal`
- **WhatsApp**: `openclaw configure --section whatsapp`

---

## 💡 使用示例

### 示例 1：浏览器自动化

**你说**：
> 打开京东，搜索"机械键盘"，截图前3个商品

**AI 会执行**：
```
1. browser open profile=chrome url="https://jd.com"
2. browser type selector=".search-input" text="机械键盘"
3. browser click selector=".search-btn"
4. browser screenshot
```

---

### 示例 2：自动比价

**你说**：
> 帮我查 Logitech G715 在京东、淘宝、拼多多的价格，做对比表

**AI 会执行**：
1. 打开京东搜索
2. 提取价格
3. 打开淘宝搜索
4. 提取价格
5. 打开拼多多搜索
6. 提取价格
7. 生成对比表格

---

### 示例 3：自动化表单

**你说**：
> 帮我填写这个表单：姓名张三，邮箱 zhangsan@example.com

**AI 会执行**：
```
1. browser navigate to [表单URL]
2. browser type selector="#name" text="张三"
3. browser type selector="#email" text="zhangsan@example.com"
4. browser click selector="#submit"
```

---

## ⚙️ 高级配置

### 1. 设置默认浏览器

编辑 `~\.openclaw\openclaw.json`：
```json
{
  "browser": {
    "defaultProfile": "chrome",
    "defaultBrowser": "chromium"
  }
}
```

### 2. 浏览器启动选项

```json
{
  "browser": {
    "headless": false,        // 显示浏览器窗口
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "slowMo": 100,            // 每个操作延迟 100ms（便于观察）
    "timeout": 30000          // 超时时间 30 秒
  }
}
```

### 3. 代理配置（可选）

```json
{
  "browser": {
    "proxy": {
      "server": "http://127.0.0.1:7890"
    }
  }
}
```

---

## 🐛 常见问题

### Q1: Gateway 启动失败
```powershell
# 检查端口占用
netstat -ano | findstr :18789

# 强制重启
openclaw gateway stop
openclaw gateway start
```

### Q2: 浏览器无法启动
```powershell
# 安装浏览器
npx playwright install chromium

# 或使用系统 Chrome
openclaw configure --section browser
# 设置 "executablePath": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
```

### Q3: Chrome 扩展连接不上
1. 确认 Gateway 已启动：`openclaw gateway status`
2. 确认扩展已附加（图标显示 ✓）
3. 尝试刷新页面
4. 检查端口是否被防火墙拦截

### Q4: 操作太慢
```json
// 调整 slowMo 参数
{
  "browser": {
    "slowMo": 0  // 去掉延迟，全速执行
  }
}
```

### Q5: 被网站反爬
- 使用 `profile=chrome`（真实用户环境）
- 手动登录网站，保存 cookies
- 降低操作速度（设置 `slowMo: 200`）
- 使用代理轮换 IP

---

## 🔐 安全建议

1. **不要在公开聊天中暴露 API Key**
2. **定期备份配置文件**：`~\.openclaw\openclaw.json`
3. **浏览器自动化时注意隐私**：不要让 AI 访问敏感页面（网银、密码管理器等）
4. **使用环境变量存储密钥**：
   ```powershell
   $env:OPENAI_API_KEY="sk-..."
   ```

---

## 📚 进阶资源

- **官方文档**: https://docs.openclaw.ai
- **GitHub**: https://github.com/openclaw/openclaw
- **技能市场**: https://clawhub.com
- **社区**: https://discord.com/invite/clawd
- **教程视频**: https://youtube.com/@openclaw（待上线）

---

## 🎯 快速测试清单

安装完成后，按顺序测试：

- [ ] `openclaw --version` 显示版本号
- [ ] `openclaw gateway status` 显示 running
- [ ] 浏览器能启动：`browser start profile=openclaw`
- [ ] 能访问网页：`browser open url="https://github.com"`
- [ ] 能截图：`browser screenshot`
- [ ] Chrome 扩展能连接（如果使用）

全部通过后，你就拥有了完整的本地 AI 助手！

---

## 🆚 对比：Windows vs VPS

| 特性 | Windows 本地 | VPS 服务器 |
|------|-------------|-----------|
| 浏览器自动化 | ✅ 完美支持 | ⚠️ 有限（headless） |
| 反爬识别 | ✅ 难被识别 | ❌ 容易被 ban |
| 可视化操作 | ✅ 能看到浏览器 | ❌ 无界面 |
| 登录状态 | ✅ 继承你的账号 | ❌ 每次全新 |
| 后台服务 | ⚠️ 需电脑开机 | ✅ 24/7 运行 |
| 性能 | ⚠️ 依赖本机 | ✅ 稳定可靠 |

**建议**：
- **浏览器任务** → Windows 本地
- **后台扫描/定时任务** → VPS 服务器

---

## 🎉 完成！

现在你可以在 Windows 上尽情使用 OpenClaw 的浏览器自动化功能了。

有问题随时问你的 AI 助手（就是我 🦞）
