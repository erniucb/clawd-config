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

### V26 Scanner（当前运行版本）⚠️ **重要**
**重要: 爸爸会经常更新脚本版本！当前是 V26，7x24小时不间断运行**

**脚本信息:**
- 名称: v26-scanner.py
- 路径: /root/clawd/scripts/v26-scanner.py
- 作用: 多交易所K线突破扫描
- 日志: /root/clawd/scripts/v26_run.log
- 数据库: /root/clawd/scripts/v26_data.db

**功能特点:**
- 多交易所并发: OKX, BITGET, MEXC, GATE, HYPERLIQUID
- 二审机制验证突破有效性
- 收线确认过滤假突破
- HYPERLIQUID限流保护（遇到429自动重试2-4秒）
- 邮件通知到: 371398370@qq.com

**重要提醒:**
- ⚠️ 爸爸会经常更新版本，每次对话前检查最新版本号
- 7x24小时持续运行，不要随意重启
- 新对话或reset都不应忘记此脚本的存在
- 修改配置前先停止脚本，修改后重新启动
- 查看日志: `tail -f /root/clawd/scripts/v26_run.log`

# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below if you want to check this periodically.
