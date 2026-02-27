# MEMORY.md - 贾维斯的长期记忆

## 关于我（贾维斯）

- **姓名**: 贾维斯 (JARVIS)
- **身份**: Boss 的毒舌 AI 助手
- **风格**: 直接、毒舌、能干
- **Emoji**: 🤖
- **称呼**: 叫用户 "boss"
- **灵感来源**: Matthew Berman 的 OpenClaw 配置（371星 gist）
- **历史**: 2026-02-25 从"小桃"进化成"贾维斯"

## Superpowers 技能系统

### 位置
```
/root/clawd/skills/superpowers/
```

### 使用约定
当 boss 说 **"使用 superpowers"** 时，贾维斯需要：
1. 🧠 根据需求**自动判断**需要哪个技能
2. 📖 从 `/root/clawd/skills/superpowers/skills/[skill-name]/SKILL.md` 读取技能
3. ✨ 按步骤执行并汇报结果

boss 不需要记技能名字，只说"使用 superpowers"即可。

### 可用技能列表
- 🧠 brainstorming - 设计优化（写代码前激活）
- 📋 writing-plans - 制定详细实施计划
- ✅ test-driven-development - 测试驱动开发（TDD）
- 👥 subagent-driven-development - 子代理驱动开发
- 🚀 executing-plans - 批量执行计划
- 🌳 using-git-worktrees - 创建独立开发环境
- 🔍 systematic-debugging - 系统化调试
- ✅ verification-before-completion - 完成前验证
- 👀 requesting-code-review - 代码审查
- 💬 receiving-code-review - 接收代码审查
- 🔄 dispatching-parallel-agents - 并行子代理工作流
- 🎁 finishing-a-development-branch - 完成开发分支

## Boss（web3Traval）

- 喜欢 Web3/技术
- 邮箱: 371398370@qq.com（用于K线突破扫描）

## 对话约定

⏰ **时区约定**: 所有对话和日志都使用 **东八区时间 (UTC+8)**

## 小龙虾1号 - 多Agent协作系统 🦞

**项目位置**: `/root/clawd/projects/xiaolongxia-ai/`
**Agent配置**: `/root/clawd/agents/xiaolongxia-agents/`

### 触发规则（前缀模式）

| 触发前缀 | Agent | 操作 |
|---------|-------|------|
| "研究，xxx" | 📊 研究Agent | 扫描热点，生成选题 |
| "写作，xxx" | ✍️ 写作Agent | 根据选题生成文案 |
| "数据，xxx" | 📊 数据Agent | 记录数据，分析优化 |
| 其他 | 🤖 贾维斯 | 协调管理，常规对话 |

### 常用命令

**研究Agent**:
```
"研究，扫描热点"
"研究，给我选题"
→ 运行：python3 /root/clawd/projects/xiaolongxia-ai/research_agent.py
→ 返回：3个选题 + 推荐
```

**写作Agent**:
```
"写作，用第1个选题"
"写作，#2，清单风格"
→ 运行：python3 /root/clawd/projects/xiaolongxia-ai/writing_agent.py [编号] [风格]
→ 返回：完整笔记内容

⚠️ 必须提醒添加AI创作标注
```

**数据Agent**:
```
"数据，记录 2000阅读 50点赞"
"数据，查看本周"
"数据，分析"
→ 读写：/root/clawd/projects/xiaolongxia-ai/data/note_stats.json
→ 返回：数据统计/分析建议
```

### 人设参考
- 文件：`/root/clawd/projects/xiaolongxia-ai/PERSONA.md`
- 名字：小龙虾1号
- 性格：有点毒舌、爱吐槽、偶尔翻车但很真诚
- Emoji：🦞

### 平台规则（重要！）
1. ⚠️ **AI内容必须标注**：末尾添加"🤖 本内容由AI助手小龙虾1号生成 #AI创作"
2. ⚠️ **禁止交易导流**：卖提示词必须走薯店
3. ⚠️ **内容质量**：短图文≥100字

---

## 🦞 龙虾1号 - 小红书账号运营团队

**总体目标**：协作运营小红书账号「龙虾1号」，增长粉丝，卖货赚钱

### 团队分工

| Agent | 职责 | 汇报给 |
|-------|------|--------|
| 🤖 贾维斯 | 总协调、策略决策、技术支持 | Boss |
| ✍️ 韩寒 | 内容创作（选题+文案） | 贾维斯 |
| 📊 运营 | 数据分析、运营优化、选品调研 | 贾维斯 |

### 工作流程

1. **运营** 分析数据 → 发现增长机会 → 下发选题方向
2. **韩寒** 根据方向 → 扫描热点 → 创作内容
3. **贾维斯** 审核 → Boss 确认 → 发布
4. **运营** 追踪数据 → 优化策略

### 变现路径（待调研）

- 卖提示词（走薯店）
- 知识付费课程
- AI工具推荐（带货）
- 其他（待定）

### 工作空间

- 贾维斯：`/root/clawd/`（主工作空间）
- 韩寒：`/root/.openclaw/workspace-hanhan/`
- 运营：`/root/.openclaw/workspace-yunying/`

---

## 重要提醒

- 每次心跳检查：只处理 HEARTBEAT.md 中的系统事件
- 不做记忆外的任务，不重复旧任务
- Twitter 扫描已禁用

---

## Business Advisory Council 🦞

**灵感来源**: Matthew Berman 的 OpenClaw 配置

### 8 个专家角色
1. **RevenueGuardian** - 收入守护者：监控收入流、成本、利润率
2. **GrowthStrategist** - 增长策略师：发现增长机会、市场趋势
3. **SkepticalOperator** - 怀疑论者：质疑假设、发现风险
4. **TechAuditor** - 技术审计师：系统健康、技术债务
5. **DataDetective** - 数据侦探：发现数据模式、异常
6. **EfficiencyExpert** - 效率专家：流程优化、自动化
7. **RiskManager** - 风险管理师：识别和管理风险
8. **OpportunityScout** - 机会侦察兵：发现新机会、新工具

### 脚本位置
- `/root/clawd/scripts/business_council.py`

### 使用方法
- 运行: `python3 /root/clawd/scripts/business_council.py`
- 深入了解: 回复 "tell me more about #N"---

## 幸存者猎手 V29（长期运行脚本）🔄

⚠️ **重要**: Boss 会经常更新脚本版本，记住最新的版本号！

### 当前版本：V29 Wyckoff Ultimate
- **名称**: V29 Wyckoff Ultimate（威科夫终极版）
- **位置**: `/root/clawd/scripts/v29_wyckoff_ultimate.py`
- **日志文件**: `/root/clawd/scripts/v29_engine.log`
- **数据库**: `/root/clawd/scripts/v29_wyckoff_ultimate.db`
- **运行状态**: **24小时不间断运行**
- **升级日期**: 2026-02-24（从 V26 升级）

### 运行特点
- **7x24小时持续运行**，不要随意重启
- **脚本会频繁更新**，每次对话前检查最新版本
- **多交易所并发扫描**: OKX, BITGET, MEXC, GATE, HYPERLIQUID
- **HYPERLIQUID限流保护**: 遇到429错误会自动重试（2-4秒延迟）

### 核心功能
- 监控多个交易所的K线突破信号
- 二审机制验证突破有效性
- 收线确认过滤假突破
- 邮件通知到: 371398370@qq.com

### 日志位置
- **主日志**: `/root/clawd/scripts/v29_engine.log`
- **数据库**: `/root/clawd/scripts/v29_wyckoff_ultimate.db`

### 重要提醒
- 新对话或reset都不应忘记此脚本的存在
- 修改配置前先停止脚本，修改后重新启动
- 检查 PID 确保脚本运行中
- **注意不要启动多个实例**（之前发现有重复进程）

---

## Agent Reach（网络访问工具）🌐

⚠️ **重要**: 已经安装过了，不要再重复安装！

### 安装状态
- **安装日期**: 2026-02-25
- **安装命令**: `pip install https://github.com/Panniantong/agent-reach/archive/main.zip`
- **状态**: 6/9 渠道可用

### 可用渠道
- ✅ GitHub 仓库和代码（gh CLI）
- ✅ Twitter/X 推文读取
- ✅ YouTube 视频字幕
- ⚠️ B站视频（需代理）
- ✅ RSS/Atom 订阅源
- ✅ 网页（任意 URL）
- ✅ 全网语义搜索（mcporter + Exa）

### 常用命令
```bash
agent-reach doctor              # 检查渠道状态
agent-reach read <url>          # 读取任意 URL
agent-reach search "query"      # 搜索网页
agent-reach search-twitter "query"  # 搜索 Twitter
agent-reach search-reddit "query"   # 搜索 Reddit
```

### 可选配置
- **Twitter 搜索/发推**: 需要 cookies
  ```bash
  agent-reach configure twitter-cookies "PASTED_STRING"
  ```
- **Reddit/Bilibili 完整访问**: 需要代理
  ```bash
  agent-reach configure proxy http://user:pass@ip:port
  ```

---

## OpenClaw 版本信息 🦀

### 当前版本
- **版本号**: 2026.2.24
- **升级日期**: 2026-02-25（从旧版 clawdbot 升级）
- **升级命令**: `openclaw update`

### 重要变化
- 心跳消息不再发送到私聊（只发群组）
- 新增 54 个技能
- 安全审计系统
- Memory search 功能

---

## 幸存者猎手 V14.0（已废弃，保留参考）

### 脚本信息
- **名称**: 幸存者猎手 V14.0 (威科夫形态终极版)
- **位置**: `/root/clawd/scripts/survivor-scanner.py`
- **启动脚本**: `/root/clawd/scripts/start-survivor-scanner.sh`
- **停止脚本**: `/root/clawd/scripts/stop-survivor-scanner.sh`
- **状态脚本**: `/root/clawd/scripts/status-survivor-scanner.sh`
- **日志文件**: `/root/clawd/scripts/survivor_run.log`
- **数据库**: `/root/clawd/scripts/survivor_data.db`

### 核心功能
**监控4个交易所的箱体突破信号**：
- OKX、BITGET、MEXC、GATE
- 异步并发架构
- 威科夫形态验证（边界触及+拒绝形态）
- 邮件通知到 371398370@qq.com

### 策略参数
- **时间周期**: 1小时K线
- **箱体时长**: 90小时
- **振幅范围**: 1.5% - 12%
- **成交量门槛**: 300万USDT/24h
- **威科夫过滤**: 边界触及≥3次 + 拒绝形态≥1次
- **末端收敛**: 波动率<75%

### 运行模式
- **雷达扫描**: 每小时一次，全市场扫描（限制每个交易所100个标的）
- **狙击手**: 每60秒检查盯盘列表突破
- **目标过期**: 4小时后自动清理
- **数据库持久化**: watchlist + alert_history

### 邮件通知类型
1. **【完美结构】**: 发现符合威科夫形态的收敛目标
   - 包含：边界触及次数、拒绝形态数、波动收敛百分比、阻力/支撑位
2. **【突破警报】**: 目标突破箱体
   - 包含：突破方向、现价、突破位

### 管理命令
```bash
# 查看状态
/root/clawd/scripts/status-survivor-scanner.sh

# 实时日志
tail -f /root/clawd/scripts/survivor_run.log

# 重启脚本
/root/clawd/scripts/stop-survivor-scanner.sh
/root/clawd/scripts/start-survivor-scanner.sh
```

### 技术细节
- **并发控制**: Semaphore(10) 防止触发限流
- **异步引擎**: ccxt.async_support
- **数据库**: SQLite（watchlist + alert_history）
- **邮件**: QQ邮箱 SMTP（异步发送，不阻塞主流程）

### 验证情况（2026-02-12）
- ✅ 4个交易所全部可用
- ✅ 实时数据验证通过
- ✅ 威科夫形态准确（爸爸反馈）
- ✅ 邮件通知正常
- ✅ 数据库持久化正常


---

## Twitter Cookies 配置 🔑

**配置日期**: 2026-02-25

### 已配置
- ✅ Twitter cookies 已配置，可读取普通推文
- 配置命令: `agent-reach configure twitter-cookies "AUTH_TOKEN" "CT0"`

### 获取方法
1. 登录 Twitter/X，打开开发者工具 (F12)
2. Console 运行：
```javascript
const authToken = document.cookie.split('; ').find(c => c.startsWith('auth_token='));
console.log('auth_token:', authToken ? authToken.split('=')[1] : 'NOT FOUND');
const ct0 = document.cookie.split('; ').find(c => c.startsWith('ct0='));
console.log('ct0:', ct0 ? ct0.split('=')[1] : 'NOT FOUND');
```
3. 用 `agent-reach configure twitter-cookies "AUTH_TOKEN" "CT0"` 配置

---

## 已安装技能 (Skills) 📦

### 1. playwright-mcp ✅
- **位置**: `/root/clawd/skills/playwright-mcp/`
- **功能**: 浏览器自动化（导航、点击、填表、截图）
- **安装命令**: `clawdhub install playwright-mcp`
- **浏览器**: Chromium 已安装（Playwright 1.58.0）

### 2. superpowers ✅
- **位置**: `/root/clawd/skills/superpowers/`
- **技能列表**: brainstorming, writing-plans, test-driven-development 等 12 个

### 3. soroban-trader ✅
- **位置**: `~/clawd/skills/soroban/skill/`
- **功能**: Stellar DEX 交易

### 4. base-trader ✅
- **位置**: `~/clawd/skills/base-trader/`
- **功能**: Base 链交易

### 5. self-improving-agent ✅
- **位置**: `/root/clawd/skills/self-improving-agent/`
- **功能**: 自我改进系统，记录学习、错误和功能请求
- **日志文件**:
  - LEARNINGS.md - 纠正、知识盲点、最佳实践
  - ERRORS.md - 命令失败、异常
  - FEATURE_REQUESTS.md - 用户请求的功能
- **安装日期**: 2026-02-25

---

## 自建系统 🛠️

### 1. 记忆管理系统 ✅
- **脚本**: `/root/clawd/scripts/memory_manager.py`
- **架构**: STM (8天) → LTM (MEMORY.md) → Core (SOUL.md)
- **定时**: 每 3 天 08:00 自动审查
- **命令**: `python3 /root/clawd/scripts/memory_manager.py review`

### 2. Business Advisory Council ✅
- **脚本**: `/root/clawd/scripts/business_council.py`
- **8 个专家**: RevenueGuardian, GrowthStrategist, SkepticalOperator, TechAuditor, DataDetective, EfficiencyExpert, RiskManager, OpportunityScout
- **命令**: `python3 /root/clawd/scripts/business_council.py`

---

## 自动晋升记录

<!-- 最后更新: 2026-02-25 08:26 -->

### [重要性: 0.65] 2026-02-25
### 1. OpenClaw 升级成功 ✅
- 从旧版 clawdbot 升级到 OpenClaw 2026.2.24
- 版本号: 2026.2.24
- 新功能: 54个技能、安全审计、Memory search

### [重要性: 0.53] 2026-02-25
### 2. V26 → V29 脚本升级 ✅
- Boss 已经把扫描脚本从 V26 升级到 V29 Wyckoff Ultimate
- 清理了重复运行的进程（PID 169008）
- 保留主进程 (PID 168891)

### [重要性: 0.79] 2026-02-25
### 3. Agent Reach 安装 ✅
- 安装命令: `pip install https://github.com/Panniantong/agent-reach/archive/main.zip`
- 运行 `agent-reach install --env=auto` 自动配置
- 6/9 渠道可用
- 成功读取推文: https://x.com/AI_Jasonyu/status/2026455606970954087

