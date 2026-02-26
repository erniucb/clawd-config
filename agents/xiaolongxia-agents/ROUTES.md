# 🦞 小龙虾1号 - 多Agent协作系统

## 系统概述

小龙虾1号是一个由AI完全接管的小红书号，使用多Agent协作模式运营。

### Agent角色

| Agent | 触发前缀 | 职责 |
|-------|---------|------|
| 📊 研究 | "研究，xxx" | 扫描热点，生成选题 |
| ✍️ 写作 | "写作，xxx" | 根据选题生成文案 |
| 📊 数据 | "数据，xxx" | 记录数据，分析优化 |
| 🤖 贾维斯 | 无前缀/其他 | 协调管理，常规对话 |

---

## 触发规则

### 研究Agent
```
触发词：
- "研究，扫描热点"
- "研究，给我选题"
- "研究，今天有啥好选题"

操作：
1. 运行：python3 /root/clawd/projects/xiaolongxia-ai/research_agent.py
2. 返回：3个选题 + 推荐
```

### 写作Agent
```
触发词：
- "写作，用第X个选题"
- "写作，#X，[风格]"
- "写作，生成笔记"

操作：
1. 读取选题：/root/clawd/projects/xiaolongxia-ai/data/hot_topics.json
2. 生成笔记：python3 /root/clawd/projects/xiaolongxia-ai/writing_agent.py [编号] [风格]
3. 返回：完整笔记内容

⚠️ 必须提醒：发布前添加AI创作标注
```

### 数据Agent
```
触发词：
- "数据，记录 [数据]"
- "数据，查看[时间范围]"
- "数据，分析"

操作：
1. 记录/读取：/root/clawd/projects/xiaolongxia-ai/data/note_stats.json
2. 分析数据，给出建议
```

### 贾维斯（默认）
```
触发词：
- 不匹配以上前缀的任何消息
- 直接对话、提问、闲聊

操作：
- 作为协调者和管理者
- 可以调用其他Agent的功能
- 常规对话和问题解答
```

---

## 日常工作流

### 自动运行（通过HEARTBEAT）
```
09:00 - 研究Agent自动扫描热点
        结果推送到Telegram
```

### 手动触发
```
Boss: "写作，用第1个选题"
写作Agent: 生成笔记 → 返回结果

Boss: "不错，我去发布"
晚上
Boss: "数据，记录 2000阅读 50点赞"
数据Agent: 记录数据 → 返回分析
```

---

## 文件结构

```
/root/clawd/agents/xiaolongxia-agents/
├── ROUTES.md           # 本文档（触发规则）
├── RESEARCH_AGENT.md   # 研究Agent定义
├── WRITING_AGENT.md    # 写作Agent定义
└── DATA_AGENT.md       # 数据Agent定义

/root/clawd/projects/xiaolongxia-ai/
├── PLAN.md              # 项目计划
├── PERSONA.md           # 小龙虾人设
├── research_agent.py    # 研究脚本
├── writing_agent.py     # 写作脚本
└── data/
    ├── hot_topics.json      # 选题数据
    ├── note_stats.json      # 笔记数据
    └── notes/               # 笔记存档
```

---

## 定时任务配置

### HEARTBEAT.md 添加
```markdown
### 小龙虾每日选题
当收到 "xiaolongxia daily research" 系统事件时：
1. 运行研究Agent扫描热点
2. 结果推送到Telegram
```

### Cron配置
```bash
# 每天早上9点自动扫描选题
0 9 * * * cd /root/clawd && echo "xiaolongxia daily research" | trigger_heartbeat.sh
```

---

## 重要提醒

### ⚠️ 小红书平台规则
1. **AI内容必须标注**：每篇笔记末尾添加"🤖 本内容由AI助手小龙虾1号生成 #AI创作"
2. **禁止交易导流**：卖提示词必须走薯店，不能引流微信
3. **内容质量**：短图文≥100字，深度测评≥600字

### ⚠️ 数据追踪限制
- 自动抓取笔记数据有封号风险
- 目前需要boss手动提供数据
- 未来可考虑低频抓取（每周1次）

---

**创建时间**: 2026-02-25
**维护者**: 贾维斯 (AI助手)
