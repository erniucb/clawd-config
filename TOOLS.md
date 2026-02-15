# TOOLS.md - Local Notes

Skills define *how* tools work. This file is for *your* specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:
- Camera names and locations
- SSH hosts and aliases  
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras
- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH
- home-server → 192.168.1.100, user: admin

### TTS
- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## 重要配置

### ⏰ 时区配置
- **所有对话时间**: 东八区 (UTC+8)
- **转换公式**: UTC时间 + 8小时 = 东八区时间
- **示例**: UTC 04:36 = 东八区 12:36

### 🔄 V26 Scanner 脚本
- **当前版本**: V26（爸爸会频繁更新，注意检查最新版本）
- **脚本路径**: `/root/clawd/scripts/v26-scanner.py`
- **日志路径**: `/root/clawd/scripts/v26_run.log`
- **数据库**: `/root/clawd/scripts/v26_data.db`
- **运行状态**: 7x24小时不间断
- **重要**: 不要随意重启，爸爸会频繁更新版本

### 📧 邮箱配置
- **突破通知邮箱**: 371398370@qq.com

### 🏦 交易所监控
- **OKX**: ✅ 就绪
- **BITGET**: ✅ 就绪
- **MEXC**: ✅ 就绪
- **GATE**: ✅ 就绪
- **HYPERLIQUID**: ✅ 就绪（有限流保护机制）
