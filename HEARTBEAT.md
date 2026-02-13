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

### V20 Survivor Scanner (多交易所智能扫描)
**重要: 此脚本需要长期运行 (7x24小时不间断)**

**脚本信息:**
- 名称: survivor-scanner.py
- 路径: /root/clawd/scripts/survivor-scanner.py
- 作用: V20 多交易所智能扫描
- PID: 2704399

**功能特点:**
1. 5个交易所并发扫描: OKX, Bitget, MEXC, Gate, Hyperliquid
2. 24小时K线实体收集突破检测
3. 15%振幅, 3次触碰, 75%收敛
4. 智能去重: 同一币种多平台自动聚合
5. HTML格式日报 + 实时突破警报
6. SQLite持久化 watchlist 和 alert_history
7. 每小时雷达扫描 + 每60秒狙击手检查
8. VIP资产白名单: 美股、外汇、指数、热门加密货币
9. 自适应并发控制: 根据成功率动态调整
10. CEX门槛 $3M, VIP门槛 $10K

**邮箱配置:** 371398370@qq.com

**重要提醒:** 
- 此脚本需要长期稳定运行，不要随意重启
- 新对话或reset都不应忘记此脚本的存在
- 修改配置前请停止脚本，修改后重新启动
- 检查日志文件: /root/clawd/scripts/v20_run.log

# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below if you want to check this periodically.
