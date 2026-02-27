---
title: "Discord消息收不到"
date: 2026-02-26
category: lessons
priority: 🟡
status: active
last_verified: 2026-02-26
tags: [discord, bug, openclaw]
---

## 问题描述
Discord bot登录成功显示在线，但完全收不到任何消息事件（私聊、群聊@都不行）。

## 排查过程
1. ✅ 检查token：正确
2. ✅ 检查Privileged Gateway Intents：全部开启
3. ✅ 重启gateway：问题依旧
4. ✅ 检查日志：只有login，没有message事件

## 根本原因
OpenClaw Discord插件的已知bug，官方还没解决。

## 证据
- GitHub Issue #24637: https://github.com/openclaw/openclaw/issues/24637
- 3天前（2026-02-23）有人报告了完全相同的问题
- Issue状态：Open（未解决）

## 解决方案
- 短期：使用Telegram（完全正常）
- 长期：等待官方修复，订阅issue获取更新

## 教训
遇到channel问题先查GitHub issues，可能是官方bug而不是配置问题。
