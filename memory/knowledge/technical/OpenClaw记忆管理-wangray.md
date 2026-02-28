# OpenClaw记忆管理

**来源**: https://x.com/wangray/status/2027034737311907870
**作者**: wangray
**类型**: 技术配置
**日期**: 2026-02-27

---

Title: Ray Wang on X: "OpenClaw 记忆管理，从入门到高阶完整实战指南" / X

URL Source: https://x.com/wangray/status/2027034737311907870

Published Time: Fri, 27 Feb 2026 10:23:05 GMT

Markdown Content:
> 一份从零到生产的实战指南，基于 5 个 Agent 协作团队 30 天的实际运行经验。

Ray Wang

@wangray

![Image 1: Article cover image](https://pbs.twimg.com/media/HAJmQXoaIAEQ-98?format=jpg&name=small)

3000字 OpenClaw 记忆系统实战：手把手搭建三层架构 + 自动衰减

我花一周时间为 OpenClaw 打磨的一套“可持久化、可检索、会衰减”的记忆架构，免费分享给大家 As usual，如果你是人类，你不想阅读，请把链接转发或者粘贴内容给你的 Agent 即可 一、为什么需要记忆架构？ 大部分...

Ray Wang

@wangray

![Image 2: Article cover image](https://pbs.twimg.com/media/HBKLs8zbUAAvwR2?format=jpg&name=small)

让 AI 记住你说过的每一句话：一套零成本记忆系统的完整构建记录

从"聊完就忘"到"结构化持久记忆"的完整迭代记录。 基于 OpenClaw 多 Agent 团队的真实生产环境，历时 17 天打磨。 为什么 Agent 需要记忆系统？ AI Agent 有一个致命缺陷：它没有真正的记忆。...

每个 LLM Agent 都有一个致命弱点：上下文窗口（Context Window）不等于记忆。

上下文窗口是临时的。当对话过长，系统会自动压缩（Compaction），丢弃早期内容。当 session 结束，一切归零。Agent 醒来时，对之前发生的事情一无所知——除非它写进了文件。

yaml

```
Session 1: 做了重要决策 A → 没写进文件 → Compaction
Session 2: Agent 完全不知道决策 A 的存在 → 重复讨论 → 浪费时间
```

这不是理论问题。在实际运行中，我们观察到：

*   Agent 在不同 session 中重复提出相同建议

*   跨频道（Telegram、Discord）的信息完全隔离

*   Compaction 后 Agent 丢失了关键上下文

我们的核心原则只有一条：

> 文件 = 事实来源。你不写进文件的东西 = 你从来不知道的东西。

Agent 的记忆不在它的"脑子"里，而在磁盘上。Context window 是工作台，文件才是仓库。

这意味着：

*   所有重要信息必须实时写入文件

*   Agent 每次启动都从文件读取状态

*   不依赖"记得去检查"，而是靠系统触发（cron、heartbeat）

我们选择了 Markdown 文件 作为记忆的主要载体，而不是纯数据库方案。原因：

yaml

```
| 维度       | Markdown 文件               | 纯数据库     |
| ---------- | --------------------------- | ------------ |
| 可解释性   | 人类可直接阅读和编辑        | 需要查询工具 |
| 调试难度   | 打开文件就能看              | 需要 SQL/API |
| 版本控制   | git 天然支持                | 需要额外方案 |
| Agent 读写 | 原生支持（Read/Write 工具） | 需要额外集成 |
| 检索效率   | 较低（需要辅助索引）        | 较高         |
```

我们的答案是 混合方案：Markdown 作为事实来源（可读层），QMD 向量数据库作为检索加速层。写入 Markdown，索引自动同步。

用途： Agent 的"工作台"，记录当前状态、优先级、阻塞项。

特点：

*   每次 heartbeat 覆写（Write），不追加

*   只保留当天的完成项

*   是 Compaction 的"救生筏"——Agent 压缩上下文后首先读这个文件

示例结构：

yaml

```
# NOW.md - Workbench
​
> 🎯 **Mission**: 你的核心目标
​
## Today (MM/DD)
- ✅ 已完成的重要事项
- ⚠️ 需要关注的问题
​
## P0 Priorities
| # | Item | Status | Owner |
|---|------|--------|-------|
| P0 | 最重要的事 | 进行中 | Agent A |
| P1 | 次重要的事 | 待开始 | Agent B |
​
## Agent Status
| Agent | Focus |
|-------|-------|
| Agent A | 当前任务 |
| Agent B | 当前任务 |
​
---
*Updated: YYYY-MM-DD HH:MM*
```

关键设计：

是唯一允许覆写的记忆文件。其他记忆文件只追加，不覆写。

用途： 事件流水，记录当天发生的一切。是记忆系统的"原始数据"。

文件名格式： memory/YYYY-MM-DD.md

写入格式：

yaml

```
### 14:30 — 完成了数据库迁移
​
迁移 PostgreSQL 从 v14 到 v16，耗时 45 分钟。
关键步骤：先备份 → 升级 → 验证数据完整性。
无数据丢失。
​
### 15:15 — Agent B 提交了周报
​
Agent B 在 Discord #reports 频道提交了本周业务报告。
要点：用户增长 12%，留存率稳定在 65%。
```

写入工具： 推荐用一个带自动时间戳的脚本（下文详述），避免手动编码时间。

关键设计：

*   追加式（append-only），永不覆写

*   不同 session 看不到彼此的对话，所以重要信息必须立刻写进日志

*   格式统一为 ### HH:MM — Title，便于扫描和检索

用途： 经过提炼的、结构化的知识库。不是原始事件，而是从事件中抽取的 可复用知识。

设计：

是导航枢纽，指向各个子目录。Agent 启动时扫描

，按需加载具体文件。

yaml

```
# Memory Vault Index
​
> Agent 启动时先扫这个文件，按需加载具体内容。
​
## Lessons
| 文件 | 优先级 | 状态 | 最后验证 | 说明 |
|------|--------|------|----------|------|
| [[cron-discipline]] | 🔴 | ✅ active | 2026-02-26 | 自动化调度经验 |
| [[infrastructure]] | 🟡 | ✅ active | 2026-02-20 | 基础设施运维 |
| [[api-integration]] | ⚪ | ⚠️ stale | 2026-01-15 | API 集成（可能过时）|
​
## Decisions
| 文件 | 说明 |
|------|------|
| [[2026-02-14-architecture-v2]] | 架构升级决策 |
​
## People
| 文件 | 优先级 | 状态 | 说明 |
|------|--------|------|------|
| [[user-profile]] | 🔴 | ✅ active | 用户画像和偏好 |
```

关键设计：

*   包含 健康度指标（优先级、状态、最后验证日期），Agent 扫描时能立即判断哪些知识可信 
*   🔴 优先级的文件 = 核心知识，永不归档

*   [⚠️ stale] 标记 = 超过 30 天未验证，信息可能过时

yaml

```
┌──────────────┐     实时写入      ┌──────────────────┐
│   对话/事件   │ ──────────────→  │  每日日志 (中期)   │
└──────────────┘                   └────────┬─────────┘
                                            │
                                    每晚 23:45 反思
                                    (提炼 + CRUD)
                                            │
                                            ▼
┌──────────────┐     每次 heartbeat  ┌──────────────────┐
│  NOW.md (短期) │ ◄──── 覆写 ─────  │ 知识库 (长期)     │
└──────────────┘                    │ lessons/          │
                                    │ decisions/        │
                                    │ people/           │
                                    └──────────────────┘
                                            │
                                    每周日 GC 归档
                                            │
                                            ▼
                                    ┌──────────────────┐
                                    │  .archive/ (冷存储) │
                                    └──────────────────┘
```

信息从上到下逐层 提炼：

1.   原始对话 → 写入日志（保留细节）

2.   日志 → 提炼到知识库（抽取可复用的教训/决策/画像）

3.   过期数据 → 归档到冷存储（释放检索空间）

yaml

```
workspace/
├── NOW.md                  # 短期：状态仪表盘（覆写式）
├── MEMORY.md               # 可选：指向 INDEX.md 的指针
├── AGENTS.md               # Agent 操作手册
├── HEARTBEAT.md            # Heartbeat 执行流程
│
└── memory/
    ├── INDEX.md            # 知识导航（启动时必读）
    ├── YYYY-MM-DD.md       # 每日日志（追加式）
    │
    ├── decisions/          # 战略决策记录
    │   └── YYYY-MM-DD-slug.md
    ├── lessons/            # 可复用教训（按主题）
    │   └── TOPIC.md
    ├── people/             # 人物/Agent 画像
    │   └── NAME.md
    ├── projects/           # 项目状态追踪
    │   └── PROJECT.md
    ├── preferences/        # 用户偏好与边界
    │   └── user-preferences.md
    ├── reflections/        # 每日自省记录
    │   └── YYYY-MM-DD.md
    ├── actions/            # 任务生命周期
    │   ├── open/
    │   ├── in-progress/
    │   └── done/           # >14 天自动归档
    │
    └── .archive/           # 冷数据（以 . 开头，搜索引擎不索引）
        ├── YYYY-MM-DD.md   # 归档的旧日志
        └── reflections/    # 归档的旧反思
```

所有 lessons/、people/、decisions/ 下的文件必须带 YAML frontmatter：

yaml

```
---
title: "Cron 调度纪律"
date: 2026-02-13                    # 创建日期
category: lessons                    # lessons | person | decision
priority: 🔴                         # 🔴 核心 | 🟡 重要 | ⚪ 参考
status: active                       # active | superseded | conflict
last_verified: 2026-02-26           # 最后确认内容仍然正确的日期
tags: [cron, automation, reliability]
---
​
## 正文内容...
```

字段说明：

yaml

```
| 字段            | 用途               | 更新时机                     |
| --------------- | ------------------ | ---------------------------- |
| `priority`      | 检索排序和归档保护 | 创建时设定，重要性变化时调整 |
| `status`        | 信息可信度标记     | CRUD 验证时更新              |
| `last_verified` | 过时检测           | 每次修改或确认内容正确时更新 |
```

状态流转：

yaml

```
active ──→ superseded    (被更新版本取代)
active ──→ conflict      (发现矛盾信息，待人工裁决)
conflict ──→ active      (人工裁决后恢复)
```

yaml

```
| 目录           | 内容                                                   | 保留策略                    |
| -------------- | ------------------------------------------------------ | --------------------------- |
| `decisions/`   | 每个重要决策一个文件，含背景、方案、理由               | **永久保留**，不归档        |
| `lessons/`     | 按主题组织的可复用经验（每个主题一个文件，追加式更新） | 🔴 永久保留；🟡⚪ 适用温度模型 |
| `people/`      | 用户画像、Agent 画像、联系人                           | **永久保留**                |
| `projects/`    | 活跃项目的状态追踪                                     | 项目结束后可归档            |
| `preferences/` | 用户的沟通偏好、工作习惯、硬性边界                     | **永久保留**                |
| `reflections/` | 每日自省（由 cron 自动生成）                           | >30 天归档                  |
| `actions/`     | 任务卡片，含优先级、截止日期、负责人                   | done/ 超 14 天归档          |
```

为什么用 . 开头的目录？

我们使用 QMD 作为语义搜索引擎。QMD 用 Bun.Glob 扫描文件时，硬编码跳过以 . 开头的目录。这意味着：

yaml

```
memory/2026-01-15.md        → QMD 会索引 ✅
memory/.archive/2026-01-15.md → QMD 自动跳过 ❌
memory/archive/2026-01-15.md  → QMD 仍会索引 ⚠️ (没有点号前缀)
```

这是一个零配置的隔离方案——不需要修改搜索引擎的配置文件或排除规则，只靠目录命名约定就实现了冷热分离。

归档的文件不会被删除，仍可通过文件系统直接访问。如果使用 Obsidian，可以在设置中开启"显示隐藏文件"来浏览归档内容。

— 日志写入脚本

bash

```
#!/usr/bin/env bash
# memlog.sh — 自动时间戳的日志追加工具
# 用法: memlog.sh "Title" "Content body"
​
set -euo pipefail
​
MEMORY_DIR="${MEMORY_DIR:-/path/to/workspace/memory}"
TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
NOW=$(TZ=Asia/Shanghai date +%H:%M)
FILE="$MEMORY_DIR/$TODAY.md"
TITLE="${1:?Usage: memlog.sh \"Title\" \"Body\"}"
BODY="${2:-}"
​
# 如果文件不存在，创建带日期标题的文件
if [[ ! -f "$FILE" ]]; then
  printf "# %s\n" "$TODAY" > "$FILE"
fi
​
# 追加带时间戳的条目
{
  printf "\n### %s — %s\n" "$NOW" "$TITLE"
  [[ -n "$BODY" ]] && printf "\n%s\n" "$BODY"
} >> "$FILE"
​
echo "✓ Logged to $TODAY.md at $NOW"
```

关键设计决策：

*   时间戳从系统时间自动获取，不需要 Agent 自己编码（避免幻觉）

*   追加式写入，永远不会覆盖已有内容

*   使用 set -euo pipefail 确保错误不会静默失败

其他写入方式：

yaml

```
| 工具                       | 用途                   | 场景                |
| -------------------------- | ---------------------- | ------------------- |
| `memlog.sh "Title" "Body"` | 日记追加（自动时间戳） | 事件、完成、决策    |
| `printf >> file`           | 追加到知识文件         | lessons/ people/ 等 |
| `Write` 工具               | 覆写                   | **仅** NOW.md       |
```

当 Agent 获得新信息时，需要判断这条信息应该写到哪里：

yaml

```
新信息到来
  │
  ├─ 是一个重大决策？ → decisions/YYYY-MM-DD-slug.md (新建)
  │
  ├─ 是一条可复用的经验？ → lessons/TOPIC.md (追加)
  │
  ├─ 是关于某个人的新信息？ → people/NAME.md (追加)
  │
  ├─ 以上都不是，但值得记录？ → memory/YYYY-MM-DD.md (日志)
  │
  └─ 无实质内容 → 不写 (NOOP)
```

经验法则： 日志可以随便写（宁多勿少），但知识文件要谨慎写（先读再写）。日志是临时的便签本，知识文件是蒸馏后的精华。

写入知识文件（lessons/、people/、decisions/）时，必须遵循 "先读再写" 原则：

yaml

```
准备写入 lessons/cron-discipline.md
  │
  ├─ Step 1: 读取目标文件当前内容
  │
  ├─ Step 2: 比较新知识与已有内容
  │     │
  │     ├─ 已有内容完全覆盖了新知识 → NOOP (跳过)
  │     │
  │     ├─ 新知识是对已有内容的更新 → UPDATE
  │     │   旧版标记: > [Superseded 2026-02-26]
  │     │   追加新版本
  │     │
  │     ├─ 新知识与已有内容矛盾 → CONFLICT
  │     │   两版都保留
  │     │   加标记: > ⚠️ CONFLICT (2026-02-26): 与上方内容矛盾
  │     │
  │     └─ 全新的知识 → ADD (追加新段落)
  │
  └─ Step 3: 更新 frontmatter 中的 last_verified 日期
```

为什么需要 CRUD 验证？

不做验证的后果是 记忆幻觉——Agent 写入了错误的、重复的、或矛盾的信息，然后在未来的检索中把这些错误信息当作事实使用。学术界称之为 HaluMem（Memory Hallucination）。

CRUD 验证是防线：每次写入前强制阅读已有内容，把冲突暴露出来而不是埋进去。

实施时机：

*   日间 heartbeat：做轻量级去重（检查目标文件末尾有没有相同内容）

*   夜间反思（23:45）：做深度 CRUD 验证（完整比对 + 分类 + 标记）

yaml

```
| 禁忌                             | 原因                                         |
| -------------------------------- | -------------------------------------------- |
| ❌ 硬编码时间戳                   | Agent 可能产生幻觉时间，用脚本自动取系统时间 |
| ❌ 用 Edit 工具修改 memory/ 文件  | Edit 可能破坏追加式工作流                    |
| ❌ 用 Write 覆写已有 memory/ 文件 | 覆写 = 数据丢失（NOW.md 除外）               |
| ❌ 写无实质内容的噪音             | "系统空闲无变化" 这种条目浪费空间和检索精度  |
| ❌ 不读就写知识文件               | 导致重复条目和记忆冲突                       |
```

yaml

```
查询到来
  │
  ├─ L1: 扫 INDEX.md → 定位目标文件 (0 cost, 纯文件读取)
  │   适用：知道要找什么类别的信息
  │   例：需要找 cron 相关经验 → INDEX.md → lessons/cron-discipline.md
  │
  ├─ L2: 直接读取目标文件 (0 cost, 纯文件读取)
  │   适用：已知具体文件路径
  │   例：读取 people/user-profile.md 获取用户偏好
  │
  └─ L3: QMD 语义搜索 (有延迟, 适合模糊查询)
      适用：不确定信息在哪个文件
      例："上次部署出过什么问题？"
```

优先走 L1/L2，L3 作为兜底。 大多数检索靠

导航就能解决，语义搜索只在不确定目标时使用。

QMD 是一个本地混合搜索引擎，结合了两种检索方式：

yaml

```
| 方式        | 技术                   | 优势                 | 劣势         |
| ----------- | ---------------------- | -------------------- | ------------ |
| BM25 关键词 | SQLite FTS5 全文索引   | 精确匹配快（~0.15s） | 不理解语义   |
| 向量语义    | sqlite-vec + embedding | 理解语义相似度       | 较慢（~12s） |
```

QMD 的 query 模式会同时执行两种搜索，然后用 LLM 做重排序（reranking），返回综合最优结果。

配置示例：

yaml

```
{
  "memory": {
    "backend": "qmd",
    "qmd": {
      "searchMode": "query",
      "update": {
        "interval": "5m",
        "onBoot": true
      },
      "limits": {
        "timeoutMs": 15000
      }
    }
  }
}
```

QMD 每 5 分钟自动重新扫描文件系统，新增/修改/删除的文件会自动更新索引。

问题： QMD 的 FTS5 使用 unicode61 tokenizer，不支持中文分词。

中文没有空格分隔词语，unicode61 会把连续汉字视为一个 token：

yaml

```
| 文档内容        | 搜索词     | FTS 结果 | 原因                                       |
| --------------- | ---------- | -------- | ------------------------------------------ |
| `盘前简报`      | `盘前简报` | ❌ 0 结果 | 文档中前后紧邻其他汉字，整体成了更长 token |
| `盘前简报`      | `盘前`     | ❌ 0 结果 | 子串不等于完整 token                       |
| `工作日记`      | `工作日记` | ✅ 有结果 | 恰好被空格/换行包围，形成独立 token        |
| `NVDA earnings` | `earnings` | ✅ 有结果 | 英文空格天然分词                           |
```

Workaround：

1.   用 query 模式（推荐）：跳过 FTS，走向量语义搜索，对中文有效但较慢

2.   写入时加空格：在中文文档中有意识地用空格分隔关键词（盘前 简报 而不是 盘前简报）

3.   未来方向：等 QMD 支持 trigram tokenizer 或 ICU 中文分词

不仅是导航表，还是知识库的 健康度仪表盘。每个条目带三个维度：

yaml

```
| 标记           | 含义             | Agent 行为         |
| -------------- | ---------------- | ------------------ |
| 🔴 priority     | 核心知识         | 优先检索，永不归档 |
| 🟡 priority     | 重要知识         | 正常检索           |
| ⚪ priority     | 参考信息         | 降权检索           |
| ✅ active       | 内容经过验证     | 正常使用           |
| ⚠️ stale        | 超过 30 天未验证 | 使用时注意可能过时 |
| 🔀 conflict     | 存在矛盾信息     | 需要人工裁决       |
| ~~superseded~~ | 已被取代         | 检索时跳过         |
```

Agent 启动时扫描

，能在几秒内了解整个知识库的健康状况。

Agent 在日间通过 heartbeat（定时心跳）和用户对话两个途径写入记忆：

yaml

```
用户对话 ──→ 做了决策/完成任务/获得新信息
                │
                ▼
         memlog.sh 写入日志
                │
                ▼
         路由判断：是否需要写入知识库？
                │
         ┌──────┴──────┐
         │  是         │  否
         ▼             ▼
    先读再写         完成
    (轻量级去重)
```

Heartbeat 是 Agent 的定时巡检机制，典型配置是每 30 分钟到 1 小时执行一次。它的核心工作：

1.   扫描所有活跃 session 的消息

2.   提取重要信息写入日志

3.   路由到对应知识文件（先读再写）

4.   刷新 
5.   检查任务生命周期

日志同步（daily-log-sync）是当天的最后一道防线，确保没有信息遗漏：

yaml

```
扫描全天所有 session（包括 heartbeat 可能遗漏的）
  │
  ▼
对比已有日志，补漏缺失的重要信息
  │
  ▼
为 23:45 的夜间反思准备完整素材
```

夜间反思（nightly-reflection）是记忆系统最核心的整合环节，相当于 人脑睡眠时的记忆整合（Consolidation）。

执行流程：

yaml

```
Step 1: 读取上下文
  ├─ 今日日志 (memory/YYYY-MM-DD.md)
  ├─ NOW.md
  └─ 相关 lessons/ 文件
​
Step 2: 写反思 (memory/reflections/YYYY-MM-DD.md)
  ├─ 计划 vs 实际发生了什么
  ├─ 什么做对了（提取可复用的模式）
  ├─ 什么做错了（提取教训）
  ├─ 学到了关于用户的什么新信息
  └─ 明天应该改变什么
​
Step 3: 清理日志
  └─ 重写当天日志：保留实质条目，去除重复和噪音
​
Step 4: CRUD 回写知识库 ← 核心步骤
  ├─ 对每条应该持久化的 insight：
  │   ├─ CLASSIFY: 分类为 [LESSON] / [PERSON] / [DECISION]
  │   ├─ READ: 读取目标文件
  │   ├─ COMPARE: ADD / UPDATE / NOOP / CONFLICT
  │   ├─ EXECUTE: 执行写入
  │   └─ METADATA: 更新 last_verified
  └─ 新文件 → 更新 INDEX.md
​
Step 5: 过时扫描
  └─ 扫描 lessons/ people/ 的 last_verified
      超过 30 天 → 标记 [⚠️ STALE]
```

为什么把 CRUD 放在夜间而不是每次写入？

*   日间写入追求速度（

< 0.01s），加 CRUD 会变成 12s（语义搜索延迟） 
*   日志是事件流，重复是正常的（同一事件从不同 session 写入）

*   知识库才需要去重和验证，而知识库的更新频率低（每天几次）

*   夜间反思有完整的一天数据，能做更准确的判断

每周一次的 GC（Garbage Collection）负责把冷数据归档到 .archive/：

bash

```
#!/usr/bin/env bash
# memory-gc.sh — 记忆垃圾回收
​
MEMORY_DIR="/path/to/workspace/memory"
ARCHIVE_DIR="$MEMORY_DIR/.archive"
​
# 规则 1: 日志 >30 天 + 近 7 天无引用 → 归档
# 规则 2: 反思 >30 天 → 归档
# 规则 3: actions/done/ >14 天 → 归档
# 规则 4: decisions/ lessons/(🔴) people/ → 永不归档
```

归档后，QMD 在下次自动重扫（≤5 分钟）时会自动将已移动的文件从索引中移除。

yaml

```
时间轴（一天）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
​
07:00  Agent 启动 → 读 NOW.md → INDEX.md → 今日日志
  │
  │    日间：heartbeat 每 30min-1h
  │    ├─ 扫描 session 消息
  │    ├─ 写日志（memlog.sh）
  │    ├─ 路由到知识文件（轻量去重）
  │    └─ 刷新 NOW.md
  │
23:30  日志同步 — 全天 session 补漏
  │
23:45  夜间反思 — 提炼 + CRUD + 过时扫描
  │
00:00  (周日) GC — 冷数据归档
​
时间轴（一周）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
​
Mon-Sat  日常写入 + 夜间反思
Sunday   夜间反思 → GC 归档 → INDEX.md 更新
```

一个只增不减的记忆系统最终会被自己淹没。经过 30 天运行，我们积累了 114 个 Markdown 文件。如果不做遗忘：

*   检索噪音增大： 向量搜索返回大量不相关的旧信息

*   启动变慢：

越来越长，扫描成本增加 
*   存储膨胀： 虽然 Markdown 文件不大，但搜索索引会持续增长

人脑的艾宾浩斯遗忘曲线告诉我们：遗忘不是 bug，是 feature。它让大脑保持高效检索的能力。

我们用"温度"（Temperature）来衡量一条记忆的活跃程度：

yaml

```
Temperature(file) = w_age × age_score + w_ref × ref_score + w_pri × priority_score
​
age_score     = exp(-0.03 × days_since_creation)    # 半衰期约 23 天
ref_score     = min(recent_references / 3, 1.0)      # 近 7 天被引用次数
priority_score = { 🔴: 1.0, 🟡: 0.5, ⚪: 0.0 }
​
权重: w_age=0.5, w_ref=0.3, w_pri=0.2
```

yaml

```
| 温度          | 状态   | 处理           |
| ------------- | ------ | -------------- |
| T > 0.7       | 🔥 Hot  | 保持在活跃索引 |
| 0.3 < T ≤ 0.7 | 🌤️ Warm | 保留但检索降权 |
| T ≤ 0.3       | 🧊 Cold | 移至 .archive/ |
```

yaml

```
| 文件类型               | 归档条件               | 保护规则               |
| ---------------------- | ---------------------- | ---------------------- |
| 日志 `YYYY-MM-DD.md`   | >30 天 + 近 7 天无引用 | 有引用则保留           |
| 反思 `reflections/`    | >30 天                 | 无                     |
| 已完成 actions `done/` | >14 天                 | 无                     |
| `decisions/`           | **永不归档**           | 战略决策是永久记录     |
| `lessons/` (🔴)         | **永不归档**           | 核心经验永久保留       |
| `lessons/` (🟡⚪)        | 温度 < 0.3 时降权标记  | 不移动，加 [COLD] 标签 |
| `people/`              | **永不归档**           | 关系记忆是核心         |
| `projects/`            | **永不归档**           | 项目追踪需要           |
| `preferences/`         | **永不归档**           | 用户偏好是核心         |
```

bash

```
# 1. 归档过期日志
for f in "$MEMORY_DIR"/202[0-9]-[0-9][0-9]-[0-9][0-9].md; do
  age_days=$(计算文件年龄)
​
  if [[ $age_days -gt 30 ]]; then
    # 检查近 7 天是否被其他文件引用（wiki-link 或日期提及）
    ref_count=$(grep -rl "$file_date" "$MEMORY_DIR"/ --include="*.md" | wc -l)
​
    if [[ $ref_count -le 0 ]]; then
      mv "$f" "$ARCHIVE_DIR/"
    fi
  fi
done
​
# 2. 归档过期反思（同理，>30 天）
​
# 3. 归档已完成 actions（>14 天，按文件修改时间）
```

关键设计：引用检查。 如果一个旧日志仍然被其他文件引用（比如某个 lesson 引用了 [[2026-01-30]]），它不会被归档。这确保了知识图谱的完整性。

GC 不是简单地"扔掉旧文件"。在实际流程中：

1.   夜间反思（23:45）已经从日志中提取了可复用知识 → 写入 lessons/

2.   GC（00:00）只归档已被反思处理过的日志

3.   如果发现某个日志没有对应的反思记录 → 标记为 [UNREFLECTED]，暂不归档

这确保了 先提炼再遗忘，知识不会因为归档而丢失。

Agent 的记忆系统面临四种"幻觉"风险（来源：HaluMem 研究）：

yaml

```
| 类型     | 描述                       | 例子                                                  |
| -------- | -------------------------- | ----------------------------------------------------- |
| **编造** | 写入从未发生过的事情       | Agent 声称"昨天做了 X"，但实际上没有                  |
| **错误** | 写入不准确的信息           | 把 A 的观点错误归因给 B                               |
| **冲突** | 同一事实的两个矛盾版本并存 | lessons/ 说"用方案 A"，但后来改成了"用方案 B"且没更新 |
| **遗漏** | 重要信息没有被记录         | 关键决策发生在对话中但没写入文件                      |
```

CRUD 验证是防止记忆幻觉的第一道防线。核心逻辑：

yaml

```
┌─────────────────────────────┐
│       新信息到来             │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  读取目标知识文件的当前内容    │
└─────────┬───────────────────┘
          │
    ┌─────┴─────┐
    │  是否有   │
    │  相似内容？│
    └─────┬─────┘
          │
    ┌─────┼─────────┐
    │     │         │
  无关   相关       矛盾
    │     │         │
    ▼     ▼         ▼
   ADD  一致？     CONFLICT
         │  │     两版保留
        是  否     加 ⚠️ 标记
         │  │
         ▼  ▼
       NOOP UPDATE
       跳过 新版追加
            旧版标记
```

每个知识文件的 frontmatter 中有 last_verified 字段。夜间反思时扫描所有文件：

bash

```
if (today - last_verified) > 30 days:
    标记 [⚠️ STALE] in INDEX.md
    下次 Agent 检索到该信息时，自动提示"此信息可能过时"
```

这不是自动删除，而是 降低置信度。Agent 仍然可以使用这些信息，但会意识到需要重新验证。

当发现矛盾时：

yaml

```
1. 两个版本都保留（不删除任何一个）
2. 新版本下方标记:
   > ⚠️ CONFLICT (2026-02-26): 与上方内容矛盾，待人工裁决
3. 该文件 frontmatter 设为 status: conflict
4. INDEX.md 中对应条目标记 🔀 conflict
5. Agent 检索到该文件时，会同时呈现两个版本
6. 等待用户裁决后，恢复为 status: active
```

设计原则： 宁可暴露冲突，不可静默覆盖。静默覆盖是记忆幻觉最危险的形式——Agent 以为自己"知道"的东西其实是错的。

的表格结构让知识库的健康状况一目了然：

yaml

```
## Lessons
| 文件 | 优先级 | 状态 | 最后验证 | 说明 |
|------|--------|------|----------|------|
| [[cron-discipline]] | 🔴 | ✅ active | 2026-02-26 | ← 最近验证，可信 |
| [[api-patterns]] | 🟡 | ✅ active | 2026-02-10 | ← 16 天前，OK |
| [[legacy-setup]] | ⚪ | ⚠️ stale | 2026-01-15 | ← 42 天，可能过时 |
| [[deploy-strategy]] | 🟡 | 🔀 conflict | 2026-02-20 | ← 有矛盾，需裁决 |
```

Agent 启动时花 2 秒扫描这张表，就能知道：

*   哪些知识可以放心使用

*   哪些需要小心验证

*   哪些需要用户介入

在多 Agent 架构中，每个 Agent 有自己的工作空间和记忆目录：

yaml

```
workspace/
├── memory/                    # 主 Agent (Atlas) 的记忆
│   ├── INDEX.md
│   ├── lessons/
│   └── ...
│
└── agents/
    ├── agent-a/
    │   └── memory/            # Agent A 的独立记忆
    │       ├── NOW.md
    │       ├── YYYY-MM-DD.md
    │       └── ...
    │
    └── agent-b/
        └── memory/            # Agent B 的独立记忆
            └── ...
```

设计原则： 每个 Agent 只读写自己的 memory/ 目录。跨 Agent 信息共享通过主 Agent 的 heartbeat 聚合。

主 Agent（协调者）在 heartbeat 时：

1.   扫描各子 Agent 的近期产出文件

2.   提取关键信息写入自己的日志

3.   跨 Agent 的洞察路由到自己的 lessons/

yaml

```
Agent A 完成了任务 → 写入 agents/agent-a/memory/2026-02-26.md
                     │
主 Agent heartbeat ──┘
  │
  ├─ 读取 Agent A 的日志
  ├─ 提取重要信息
  └─ 写入主 memory/2026-02-26.md
```

LLM Agent 的一个关键约束：不同 session 之间完全隔离。

Agent 在 Telegram 上和用户的对话是一个 session，在 Discord 上的对话是另一个 session。它们看不到彼此的内容。

解决方案： 文件是唯一的跨 session 通道。任何在一个 session 中获得的重要信息，必须立刻写入文件，这样其他 session 才能访问。

yaml

```
Session A (Telegram): 用户说"以后用方案 B" → 立刻 memlog.sh 记录
Session B (Discord): 读取今日日志 → 知道了这个决策
```

如果你只想快速跑起来，最少需要 3 个文件：

yaml

```
workspace/
├── NOW.md           # 状态板
├── AGENTS.md        # Agent 操作手册（含记忆规则）
└── memory/
    └── YYYY-MM-DD.md  # 每日日志
```

— 每次对话开始时读取，了解当前状态：

markdown

```
# NOW.md
​
## Today
- 当前在做什么
- 优先级是什么
​
---
*Updated: YYYY-MM-DD HH:MM*
```

— 告诉 Agent 如何操作记忆：

markdown

```
## Session Startup
1. Read NOW.md
2. Read memory/YYYY-MM-DD.md (today)
​
## Memory Rules
- 完成任务/做决策时，写入 memory/YYYY-MM-DD.md
- 格式: ### HH:MM — Title
- NOW.md 每次对话结束时更新
```

memory/YYYY-MM-DD.md — 日志，追加式写入。

这就是最小可用的记忆系统。Agent 启动时知道当前状态，对话中的重要信息会被记录，下次启动时能恢复上下文。

yaml

```
阶段 0（立刻）
  ├─ NOW.md + AGENTS.md + 每日日志
  └─ 效果：基本的跨 session 记忆
​
阶段 1（第 1 周）
  ├─ 增加 INDEX.md
  ├─ 增加 lessons/ 和 decisions/ 目录
  ├─ 增加 memlog.sh 自动时间戳脚本
  └─ 效果：结构化知识积累
​
阶段 2（第 2 周）
  ├─ 增加 Frontmatter 规范 (priority / status / last_verified)
  ├─ 增加 HEARTBEAT.md（定时巡检流程）
  ├─ 启用夜间反思 cron（CRUD 回写）
  └─ 效果：知识质量保障
​
阶段 3（第 3 周）
  ├─ 增加 QMD 语义搜索
  ├─ 增加 memory-gc.sh（冷数据归档）
  ├─ 增加 .archive/ 冷存储
  └─ 效果：检索效率 + 主动遗忘
​
阶段 4（第 4 周+）
  ├─ 多 Agent 协作记忆
  ├─ 自动过时检测
  ├─ 冲突处理流程
  └─ 效果：完整的生产级记忆系统
```

建议：不要一次性搭全。 从阶段 0 开始，每周加一层。每个阶段都是可独立运行的，不需要后续阶段也能工作。

我们的记忆系统天然兼容 Obsidian，因为它就是一堆 Markdown 文件。

配置建议：

1.   将 memory/ 目录设为 Obsidian vault

2.   启用以下核心插件： File explorer（文件浏览） Graph view（知识图谱可视化） Backlinks（反向链接） Daily notes（每日笔记模板） Properties（YAML frontmatter 可视化）

3.   设置 useMarkdownLinks: false，启用 [[wiki-link]] 语法

4.   设置 newLinkFormat: "shortest"，自动生成最短路径

5.   如需浏览归档内容，在设置中开启"显示隐藏文件"

Graph View 的价值： 通过 Obsidian 的知识图谱，你可以可视化 decisions/、lessons/、people/ 之间的引用关系，发现潜在的知识关联。

本记忆系统的设计借鉴了多个来源：

yaml

```
| 来源                           | 借鉴点                                           |
| ------------------------------ | ------------------------------------------------ |
| **人脑记忆整合**               | 短→中→长期分层；睡眠时整合（nightly-reflection） |
| **艾宾浩斯遗忘曲线**           | 时间衰减模型；主动遗忘保持效率                   |
| **Stanford Generative Agents** | recency × importance × relevance 三维检索评分    |
| **ACT-R 认知架构**             | 记忆激活公式：基础激活 + 上下文关联              |
| **Mem0**                       | ADD/UPDATE/DELETE/NOOP 自适应 CRUD               |
| **MemGPT (Letta)**             | 虚拟内存概念；核心记忆 vs 归档记忆               |
| **HaluMem**                    | 记忆幻觉分类；写入验证的必要性                   |
| **TiMem**                      | 时间层次化记忆树                                 |
| **EVOLVE-MEM**                 | 三层自适应提炼（原始经验 → 摘要 → 原则）         |
```

这套系统从一个只有 3 个文件的最小配置起步，经过 30 天的实际运行迭代到了当前状态。它不是一次性设计出来的，而是在解决真实问题（Compaction 丢信息、搜索找不到、知识过时、记忆冲突）的过程中逐步演进的。

如果你也在给自己的 Agent 搭记忆系统，从阶段 0 开始。遇到问题时再加层。

