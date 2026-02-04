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

# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below if you want to check this periodically.
