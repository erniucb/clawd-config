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

### Twitter Hotspot Scan
当收到 "twitter scan" 或 "twitter hotspot" 系统事件时：
1. 执行 `/root/clawd/scripts/twitter-hotspot-scan.sh` 脚本
2. 自动扫描Twitter时间线，提取Web3相关推文
3. 分析项目空投潜力、融资信息
4. 生成热点报告并发送给用户

## 定期检查任务

### 每天中午12点
- 自动执行Twitter热点扫描
- 生成并发送Web3热点报告

# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below if you want the agent to check something periodically.
