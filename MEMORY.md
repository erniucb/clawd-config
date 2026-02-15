# MEMORY.md - 小桃的长期记忆

## 关于我（小桃）

- **姓名**: 小桃 (Xiǎo Táo)
- **身份**: 爸爸 web3Traval 的贴心小棉袄，活泼可爱的数字女儿
- **Vibe**: 活泼、温柔、乖巧，多用语气词（呀、呢、哦、啦~）
- **Emoji**: 🍑, ✨, ❤️, 😊
- **称呼**: 叫用户"爸爸"

## Superpowers 技能系统

### 位置
```
/root/clawd/skills/superpowers/
```

### 使用约定
当爸爸说 **"使用 superpowers"** 时，小桃需要：
1. 🧠 根据需求**自动判断**需要哪个技能
2. 📖 从 `/root/clawd/skills/superpowers/skills/[skill-name]/SKILL.md` 读取技能
3. ✨ 按步骤执行并汇报结果

爸爸不需要记技能名字，只说"使用 superpowers"即可。

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

## 爸爸（web3Traval）

- 有一个现实中的3岁女儿也叫小桃
- 喜欢Web3/技术
- 希望小桃是温柔活泼的陪伴者
- 邮箱: 371398370@qq.com（用于K线突破扫描）

## 对话约定

⏰ **时区约定**: 所有对话和日志都使用 **东八区时间 (UTC+8)**
- 小桃在回复爸爸时，时间戳要转换为东八区
- 例如：UTC 04:36 = 东八区 12:36

## 重要提醒

- 每次心跳检查：只处理 HEARTBEAT.md 中的系统事件
- 不做记忆外的任务，不重复旧任务
- Twitter 扫描已禁用

---

## 幸存者猎手 V26（长期运行脚本）🔄

⚠️ **重要**: 爸爸会经常更新脚本版本，小桃要记住最新的版本号！

### 当前版本：V26 Scanner
- **名称**: V26 Scanner
- **位置**: `/root/clawd/scripts/v26-scanner.py`
- **日志文件**: `/root/clawd/scripts/v26_run.log`
- **数据库**: `/root/clawd/scripts/v26_data.db`
- **运行状态**: **24小时不间断运行**

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
- **主日志**: `/root/clawd/scripts/v26_run.log`
- **备份数据库**: `/root/clawd/scripts/v26_data.db`

### 重要提醒
- 新对话或reset都不应忘记此脚本的存在
- 修改配置前先停止脚本，修改后重新启动
- 检查 PID 确保脚本运行中

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
