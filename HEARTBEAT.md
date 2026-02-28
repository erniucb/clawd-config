# HEARTBEAT.md

## 系统事件处理

### GitHub Sync
当收到 "github sync" 系统事件时：
1. 执行 `/root/clawd/scripts/sync-github.sh` 脚本
2. 向用户报告同步结果

### Gateway Restart
当收到 "gateway restart" 系统事件时：
1. 执行 `clawdbot gateway restart` 命令
2. 向用户报告重启结果

### Twitter Hotspot Scan (已禁用)
此功能已关闭 - Twitter 扫描脚本存在访问问题

### K线突破扫描
当收到 "kline breakout scan" 系统事件时：
1. 执行 `/root/clawd/scripts/scan-breakout-email.sh` 脚本
2. 检测4小时K线突破，如有符合条件的发送邮件到 371398370@qq.com

### Bitget PowerUSDT 15分钟K线实体收集突破监控
当收到 "bitget powerusdt scan" 系统事件时：
1. 启动 `/root/clawd/scripts/bitget-powerusdt-sync.py` 脚本
2. 监控 POWERUSDT 15分钟K线实体收集突破
3. 检测24小时震荡区间突破（42%阈值）
4. 发送邮件到 371398370@qq.com

### V29 Wyckoff Ultimate（当前运行版本）⚠️ **重要**
**重要: Boss 会经常更新脚本版本！当前是 V29，7x24小时不间断运行**

**脚本信息:**
- 名称: v29_wyckoff_ultimate.py
- 路径: /root/clawd/scripts/v29_wyckoff_ultimate.py
- 作用: 威科夫形态终极版扫描器
- 日志: /root/clawd/scripts/v29_engine.log
- 数据库: /root/clawd/scripts/v29_wyckoff_ultimate.db

**功能特点:**
- 多交易所并发: OKX, BITGET, MEXC, GATE, HYPERLIQUID
- 二审机制验证突破有效性
- 收线确认过滤假突破
- HYPERLIQUID限流保护（遇到429自动重试2-4秒）
- 邮件通知到: 371398370@qq.com

**重要提醒:**
- ⚠️ Boss 会经常更新版本，每次对话前检查最新版本号
- 7x24小时持续运行，不要随意重启
- 新对话或reset都不应忘记此脚本的存在

### 赚钱项目检查提醒（2026-03-01）

**下次检查时间**：2026-03-01（周六）

**检查内容**：
1. 网盘资源赚佣金 - 是否找到热门资源？
2. AI产品推广 - 是否看了神图君教程？
3. 流量卡/外卖券 - 是否找到渠道？

**提醒Boss**：赚钱灵感库在 `/root/clawd/memory/business/赚钱灵感库.md`
- 修改配置前先停止脚本，修改后重新启动
- 查看日志: `tail -f /root/clawd/scripts/v29_engine.log`

### Memory Review（记忆审查）
当收到 "memory review" 系统事件时：
1. 运行 `python3 /root/clawd/scripts/memory_manager.py review`
2. 检查短期记忆，晋升重要条目到长期记忆
3. 归档过期记忆文件
4. 向 boss 报告审查结果

### 小龙虾1号 - 每日选题扫描 🦞
当收到 "xiaolongxia research" 系统事件时：
1. 运行研究Agent扫描热点：
   ```bash
   cd /root/clawd/projects/xiaolongxia-ai
   python3 research_agent.py
   ```
2. 读取生成的选题：`/root/clawd/projects/xiaolongxia-ai/data/hot_topics.json`
3. 向boss推送今日选题（格式化输出）

**定时配置（可选）**：
- 每天9:00自动运行（通过cron触发）

# 心跳检查任务

## 每次心跳必查

1. **检查今日待办**：`/root/clawd/memory/todo/YYYY-MM-DD.md`
   - 如果有高优先级未完成事项，提醒boss

2. **V29脚本状态**：确认运行正常

---

# Keep this file empty (or with only comments) to skip heartbeat API calls.
