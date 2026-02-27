---
title: "小红书发帖需要浏览器插件"
date: 2026-02-26
category: lessons
priority: 🟡
status: pending
last_verified: 2026-02-26
tags: [xiaohongshu, x-mcp, setup]
---

## 背景
想在服务器上自动化发小红书，但Docker版的xiaohongshu-mcp需要图形界面扫码登录。

## 问题
- 服务器没有X server
- 登录工具启动失败：`Missing X server or $DISPLAY`
- MCP服务正常，但无法获取二维码

## 解决方案
**x-mcp浏览器插件版**（推荐）
- 在本地电脑浏览器安装插件
- 复用浏览器的小红书登录状态
- 不需要服务器部署

## 安装步骤
1. 安装Chrome插件：[小红书MCP助手](https://chromewebstore.google.com/detail/...)
2. 注册 https://x.zouying.work/ 获取API Token
3. 在插件中填入Token
4. 配置OpenClaw连接到 `https://mcp.zouying.work/mcp`

## 状态
⏳ 等待Boss获取API Token

## 备注
- Docker版已部署但暂停使用（需要图形界面）
- x-mcp版更适合非技术用户
