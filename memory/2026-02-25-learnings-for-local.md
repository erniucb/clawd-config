# 2026-02-25 学习笔记（供本地 OpenClaw 学习）

> 本文档由 VPS 贾维斯整理，包含今天的学习内容和经验教训

---

## 📚 技能安装

### 1. self-improving-agent 技能

**技能描述**：
- 自动记录学习、错误和功能请求
- 帮助 AI 助手持续改进
- 包含日志系统和 Hook 机制

**安装方法**：
```bash
# 方式1：ClawHub（推荐）
clawdhub install pskoett/self-improving-agent

# 方式2：手动安装（如果 ClawHub 限流）
cd /path/to/skills/
git clone https://github.com/pskoett/self-improving-agent.git
mkdir -p .learnings
cp skills/self-improving-agent/assets/LEARNINGS.md .learnings/
```

**相关链接**：
- ClawHub 页面: https://clawhub.ai/pskoett/self-improving-agent
- GitHub 仓库: https://github.com/pskoett/self-improving-agent

**学习要点**：
- 创建 `.learnings/` 目录存放日志文件
- 三类日志：LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md
- 重要学习可晋升到 MEMORY.md 或技能文件

---

## 🌐 GitHub 搜索结果

### 搜索词：openclaw

**前3个结果**：

1. **openclaw/openclaw** ⭐ 228k
   - 简介: "Your own personal AI assistant. Any OS. Any Platform. The lobster way. 🦞"
   - 语言: TypeScript
   - 更新: 47 分钟前
   - 链接: https://github.com/openclaw/openclaw
   - **这是本体仓库**

2. **HKUDS/nanobot** ⭐ 24.9k
   - 简介: "🐈 nanobot: The Ultra-Lightweight OpenClaw"
   - 语言: Python
   - 更新: 11 小时前
   - 链接: https://github.com/HKUDS/nanobot
   - **香港大学的轻量版**

3. **VoltAgent/awesome-openclaw-skills** ⭐ 19.9k
   - 简介: "The awesome collection of OpenClaw Skills. Formerly known as Moltbot, originally Clawdbot."
   - 更新: 昨天
   - 链接: https://github.com/VoltAgent/awesome-openclaw-skills
   - **技能合集**

**其他相关仓库**：
- [openclaw/clawhub](https://github.com/openclaw/clawhub) ⭐ 2.8k - Skill Directory
- [hesamsheikh/awesome-openclaw-usecases](https://github.com/hesamsheikh/awesome-openclaw-usecases) ⭐ 7.5k - 用例合集
- [cloudflare/moltworker](https://github.com/cloudflare/moltworker) ⭐ 9.2k - Cloudflare Workers 版本

---

## 🛒 亚马逊机械键盘搜索结果

### 搜索词：mechanical keyboard

**按评分排序，前3个高评分产品**：

1. **Logitech G715 Wireless Mechanical Gaming Keyboard** ⭐ #1 Top Rated
   - 价格: **$129.99**（原价 $219.99，打6折）
   - 评分: 标记为 "#1 Top Rated"
   - 特点: LIGHTSYNC RGB, Lightspeed 无线, GX Red 线性轴, 配套掌托
   - 颜色: White Mist
   - 亚马逊链接: https://www.amazon.com/dp/B09LK1P1RD

2. **SOLAKAKA KI99 Pro 96% Wireless Mechanical Keyboard** ⭐ 4.7/5
   - 价格: **$66.89**（原价 $75.89）
   - 评分: 4.7星（196评价）
   - 特点: 96%布局, RGB, 热插拔预润滑轴, Gasket 结构
   - 卖点: "Creamy Keyboard"（柔和手感）
   - 亚马逊链接: 搜索 "SOLAKAKA KI99 Pro"

3. **EPOMAKER X Aula F75 MAX Wireless Mechanical Keyboard**
   - 价格: **$70.54**（原价 $82.99）
   - 销量: 1000+ 上月购买
   - 特点: TFT 彩色屏幕, 旋钮控制, 75%布局, 热插拔, RGB背光
   - 亚马逊链接: 搜索 "EPOMAKER F75 MAX"

**经验教训**：
- 浏览器服务挂了时，可以用 `web_fetch` 抓取静态内容
- 亚马逊的反爬相对宽松，能抓到基本数据
- 但价格和评分信息有时不完整

---

## ❌ 失败任务：电商比价

### 任务：京东/淘宝/拼多多比价

**目标**：对比 Logitech G715 在三大平台的价格

**结果**：**全部失败**

**失败原因**：
1. **京东**：跳转到首页，返回空内容
2. **淘宝**：返回 "搜同款" 三个字，无实际数据
3. **拼多多**：直接报错 "fetch failed"

**尝试方案**：
- ❌ `web_fetch` - 反爬拦截
- ❌ Playwright 脚本 - 超时（京东10秒，淘宝30秒）
- ❌ Agent Reach - 进程被 SIGTERM 杀死
- ❌ 浏览器工具 - Gateway CDP 端口不通

**根本原因**：
- VPS 服务器环境，无真实用户特征
- IP 被标记为爬虫
- headless 浏览器容易被识别

**解决方案**：
- ✅ **Windows 本地环境**：真实浏览器，真实用户代理，继承登录状态
- ✅ Chrome 扩展模式：操作已登录的标签页
- ✅ 降低操作速度，设置 `slowMo` 延迟

---

## 🖥️ 浏览器自动化测试

### VPS 环境测试结果

| 工具 | 状态 | 备注 |
|------|------|------|
| OpenClaw browser tool | ❌ 失败 | CDP 端口不通，服务未启动 |
| Playwright | ⚠️ 部分可用 | 能运行但被反爬拦截 |
| Agent Reach | ❌ 失败 | 进程被杀 |
| web_fetch | ⚠️ 受限 | 静态页面可用，电商网站拦截 |

**Gateway 状态**：
```bash
openclaw gateway status
# Runtime: running (pid 260025)
# RPC probe: ok
# 但浏览器 CDP 端口（18792）无法连接
```

**结论**：
- VPS 环境下浏览器自动化**基本不可用**
- 适合后台服务（如 V29 扫描脚本）
- 不适合需要真实浏览器环境的任务

---

## 🆚 Windows vs VPS 对比

| 特性 | Windows 本地 | VPS 服务器 |
|------|-------------|-----------|
| **浏览器自动化** | ✅ 完美支持 | ⚠️ 有限（headless） |
| **反爬识别** | ✅ 难被识别 | ❌ 容易被 ban |
| **可视化操作** | ✅ 能看到浏览器 | ❌ 无界面 |
| **登录状态** | ✅ 继承你的账号 | ❌ 每次全新 |
| **Chrome 扩展** | ✅ 可附加标签页 | ❌ 不可用 |
| **后台服务** | ⚠️ 需电脑开机 | ✅ 24/7 运行 |
| **性能稳定性** | ⚠️ 依赖本机 | ✅ 稳定可靠 |
| **成本** | ✅ 免费 | ⚠️ 需付服务器费用 |

**最佳实践**：
- **浏览器任务**（比价、爬虫、自动化）→ Windows 本地
- **后台扫描**（定时任务、监控脚本）→ VPS 服务器

---

## 📖 Windows 安装指南

### 文档位置
- VPS 路径: `/root/clawd/docs/OPENCLAW_WINDOWS_GUIDE.md`
- 可复制到本地使用

### 快速安装步骤

```powershell
# 1. 安装 Node.js
winget install OpenJS.NodeJS.LTS

# 2. 安装 OpenClaw
npm install -g openclaw

# 3. 配置 AI 模型
openclaw configure --section ai

# 4. 启动 Gateway
openclaw gateway start

# 5. 验证
openclaw status
```

### 浏览器使用方式

**方式 1：独立浏览器**
```
browser start profile=openclaw
browser open url="https://github.com"
```

**方式 2：连接现有 Chrome（推荐）** ⭐
1. 安装 OpenClaw Chrome 扩展
2. 在浏览器任意标签页点击扩展图标
3. AI 可以操作已登录的页面

**示例对话**：
```
你：打开京东搜索机械键盘
AI：browser open profile=chrome url="https://jd.com"
```

### 重要提示
- Windows 本地有**真实浏览器环境**
- 可以继承你的登录状态（京东、淘宝等）
- AI 操作时你能看到，可监控
- 不容易被反爬识别

---

## 🔧 技术细节

### Gateway 配置

**VPS 环境**：
```
Gateway: 127.0.0.1:18789
Chrome CDP: 127.0.0.1:18792 (不工作)
Dashboard: http://127.0.0.1:18789/
```

**Windows 环境应该类似**：
```
Gateway: 127.0.0.1:18789
Chrome CDP: 127.0.0.1:18792
```

### 常用命令

```bash
# 查看状态
openclaw gateway status

# 重启 Gateway
openclaw gateway restart

# 查看日志
tail -f /tmp/openclaw/openclaw-2026-02-25.log

# 检查浏览器
browser status
browser profiles
```

---

## 📝 经验总结

### 1. 电商网站反爬策略
- **京东**：检查 User-Agent、IP 频率、JavaScript 环境
- **淘宝**：复杂的滑块验证、行为分析
- **拼多多**：严格的 API 限制

### 2. 破解方案
- ✅ 使用真实浏览器环境（Windows 本地）
- ✅ 继承已登录的 cookies
- ✅ 降低爬取速度
- ✅ 使用代理轮换 IP（高级方案）

### 3. 工具选择
- **静态页面**：`web_fetch` 够用
- **动态页面**：Playwright（本地环境）
- **需要登录**：Chrome 扩展模式（profile=chrome）
- **后台监控**：VPS + 定时脚本

### 4. 调试技巧
- 检查 Gateway 状态：`openclaw gateway status`
- 查看浏览器进程：`ps aux | grep chrome`
- 测试 CDP 端口：`curl http://127.0.0.1:18792/json`
- Playwright 调试：`npx playwright --version`

---

## 🔗 相关资源链接

### OpenClaw 官方
- **主仓库**: https://github.com/openclaw/openclaw
- **官方文档**: https://docs.openclaw.ai
- **技能市场**: https://clawhub.ai
- **社区 Discord**: https://discord.com/invite/clawd

### 技能相关
- **self-improving-agent**: https://clawhub.ai/pskoett/self-improving-agent
- **GitHub 仓库**: https://github.com/pskoett/self-improving-agent

### 相关仓库
- **轻量版 nanobot**: https://github.com/HKUDS/nanobot
- **技能合集**: https://github.com/VoltAgent/awesome-openclaw-skills
- **用例合集**: https://github.com/hesamsheikh/awesome-openclaw-usecases

### 工具文档
- **Playwright**: https://playwright.dev
- **MCP Protocol**: https://modelcontextprotocol.io
- **Brave Search API**: https://brave.com/search/api/

---

## 🎯 给本地 OpenClaw 的建议

### 1. 环境配置
- ✅ 使用 Chrome 扩展模式（profile=chrome）
- ✅ 手动登录常用网站（京东、淘宝）
- ✅ 设置 `slowMo: 100` 便于观察

### 2. 技能安装
```bash
# 安装 self-improving-agent
clawdhub install pskoett/self-improving-agent

# 创建学习日志
mkdir -p .learnings
```

### 3. 日常使用
- 浏览器任务：直接说"打开浏览器..."
- 比价任务：先手动登录，再让 AI 操作
- 后台任务：考虑跑在 VPS 上

### 4. 调试技巧
- 遇到问题先检查 Gateway 状态
- 浏览器问题尝试重启 Gateway
- 查看 `~/.openclaw/` 目录下的日志

---

## 📊 今日任务完成度

| 任务 | 状态 | 备注 |
|------|------|------|
| GitHub 搜索 openclaw | ✅ 完成 | 找到3个主要仓库 |
| 亚马逊机械键盘搜索 | ✅ 完成 | 找到3个高评分产品 |
| 京东/淘宝/拼多多比价 | ❌ 失败 | 反爬拦截，需本地环境 |
| 浏览器自动化测试 | ⚠️ 部分 | VPS 环境受限 |
| self-improving-agent 安装 | ✅ 完成 | 技能已就绪 |
| Windows 安装指南 | ✅ 完成 | 文档已生成 |

**总体完成度**: 4/6 (67%)

---

## 💡 下次优化方向

1. **本地环境测试**：
   - 在 Windows 本地重试电商比价
   - 测试 Chrome 扩展模式
   - 验证浏览器自动化能力

2. **技能完善**：
   - 安装更多实用技能
   - 配置学习 Hook
   - 建立学习晋升机制

3. **文档完善**：
   - 补充本地环境配置细节
   - 记录更多使用案例
   - 整理常见问题解答

---

**生成时间**: 2026-02-25 14:25 UTC
**生成者**: VPS 贾维斯 🤖
**目标读者**: Windows 本地 OpenClaw 实例
