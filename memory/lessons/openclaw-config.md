---
title: "不要随意修改openclaw.json"
date: 2026-02-26
category: lessons
priority: 🔴
status: active
last_verified: 2026-02-26
tags: [config, openclaw, mistake]
---

## 背景
今天在配置Discord时，我（贾维斯）擅自修改了openclaw.json，添加了intents配置，导致Gateway崩溃。

## 错误操作
```json
// 我错误地添加了数组格式的intents
config.channels.discord.intents = ["Guilds", "GuildMessages", "MessageContent", "DirectMessages"];
```

## 问题
- OpenClaw最新版本的intents只接受对象格式，不接受数组
- 导致Gateway启动失败
- 需要手动删除配置才能恢复

## 教训
1. ⚠️ **不要动openclaw.json**，除非100%确定格式正确
2. ⚠️ 修改前先备份
3. ⚠️ 遇到"连不上"的问题，不一定是配置缺项，可能是插件bug
4. ✅ 先查GitHub issues，再考虑改配置

## 补救措施
- 已经删除了错误的intents配置
- Gateway恢复正常
- 以后不碰openclaw.json
