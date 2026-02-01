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

## 定期检查任务

# Keep this file empty (or with only comments) to skip heartbeat API calls.
# Add tasks below when you want the agent to check something periodically.
