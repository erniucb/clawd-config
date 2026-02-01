# Clawdbot 配置备份

这个仓库包含 `/root/clawd` 目录的完整备份，用于版本控制和一键回滚。

## 自动同步

### 定时任务
- **每天凌晨2点**: 自动重启Gateway服务
- **每天凌晨3点**: 自动同步GitHub（拉取+推送）

### 如何使用

#### 从GitHub恢复配置
```bash
cd /root/clawd
git pull origin master
```

#### 手动推送更改
```bash
cd /root/clawd
git add -A
git commit -m "描述你的更改"
git push origin master
```

#### 一键回滚到某个版本
```bash
cd /root/clawd
# 查看历史
git log --oneline

# 回滚到指定版本（例如：4173f29）
git reset --hard <commit-hash>

# 如果需要，推送回滚（谨慎使用！）
git push origin master --force
```

## 目录结构

```
/root/clawd/
├── AGENTS.md          # Agent工作空间规则
├── SOUL.md           # 小桃的人格设定
├── IDENTITY.md       # 身份配置
├── USER.md           # 用户信息
├── TOOLS.md          # 工具配置
├── HEARTBEAT.md      # 心跳任务
├── kindergarten-ppt/  # 幼儿园PPT生成技能
├── web3-dev/         # Web3开发技能
└── scripts/          # 自动化脚本
    └── sync-github.sh # GitHub同步脚本
```

## 注意事项

⚠️ **安全提醒**:
- 这个仓库是公开的，请勿提交敏感信息（密码、token、私钥等）
- GitHub token应该通过环境变量或Git credential manager管理
- 定期检查仓库内容，避免意外泄露

🔄 **版本管理**:
- 每次自动同步都会带上时间戳的提交信息
- 重要修改建议手动提交时写清楚说明
- 回滚前先备份当前状态

## 维护者

小桃 (Xiǎo Táo) - 贴心小助手 🍑
