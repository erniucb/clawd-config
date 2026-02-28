# 贾维斯知识库系统

> 让学习到的知识跨session可用，并在创作/问答时自动检索

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    知识输入（你发的推文/文章）                 │
│                            ↓                                │
│                    贾维斯分类 + 存储                         │
│                            ↓                                │
├─────────────────────────────────────────────────────────────┤
│  第一层：知识库（结构化存储）                                 │
│  ├── writing-styles/    # 写作风格范例                       │
│  ├── tutorials/         # 教程（OpenClaw配置等）             │
│  ├── product-knowledge/ # 产品知识（OpenClaw功能/优势）      │
│  ├── business/          # 商业知识（赚钱场景/变现路径）       │
│  ├── technical/         # 技术知识（API/配置/调试）          │
│  └── feedback/          # 用户反馈/痛点                      │
├─────────────────────────────────────────────────────────────┤
│  第二层：索引（KNOWLEDGE_INDEX.md）                          │
│  - 所有知识文件的目录                                        │
│  - 按主题分类                                                │
│  - 标注优先级和更新时间                                      │
├─────────────────────────────────────────────────────────────┤
│  第三层：核心摘要（MEMORY.md + SOUL.md）                     │
│  - 最常用的知识提炼到核心文件                                │
│  - 每次session启动时自动加载                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 检索机制

### 方案A：索引 + 主动加载（当前可行）

**原理**：
1. 所有知识存在 `memory/knowledge/` 分类目录
2. `KNOWLEDGE_INDEX.md` 维护完整索引
3. 新session启动时：
   - 读 `KNOWLEDGE_INDEX.md`（知道有什么）
   - 根据任务类型，主动加载相关知识文件
   - 例如：创作任务 → 加载 `writing-styles/` 所有文件

**优点**：
- 不依赖外部API
- 100%可控
- 知识结构清晰

**缺点**：
- 需要主动判断加载什么
- 知识多时token消耗大

### 方案B：语义搜索（未来）

**原理**：
1. 用embedding把知识向量化
2. 存到向量数据库（Pinecone/Chroma）
3. 问答/创作时，语义检索相关知识

**优点**：
- 自动化程度高
- 精准检索

**缺点**：
- 需要配置embedding服务
- 依赖外部API

**当前建议**：先用方案A，等技术成熟后再升级方案B

---

## 与子代理共享

**问题**：韩寒/运营看不到主session的知识

**解决方案**：

1. **共享目录**：`/root/clawd/memory/knowledge/` 
   - 主session写入
   - 子代理可读

2. **任务传递时附带知识**：
   ```
   sessions_spawn(
     task: "...",
     knowledge: "参考以下知识：[知识摘要]"
   )
   ```

3. **韩寒workspace软链接**：
   ```bash
   ln -s /root/clawd/memory/knowledge /root/.openclaw/workspace-hanhan/knowledge
   ```

---

## 知识写入规则

### 自动分类

| 内容类型 | 存储位置 | 示例 |
|----------|----------|------|
| 优质推文/文章 | `writing-styles/` | OneHopeA9的OpenClaw长文 |
| 配置教程 | `tutorials/` | OpenClaw安装配置指南 |
| 产品功能/优势 | `product-knowledge/` | OpenClaw的17个场景 |
| 变现场景 | `business/` | 如何用OpenClaw赚钱 |
| API/配置 | `technical/` | 6651 API使用方法 |
| 用户吐槽/痛点 | `feedback/` | "配置太复杂" |

### 写入流程

```bash
# 1. boss发来优质内容
# 2. 贾维斯分析并分类
# 3. 存储到对应目录
/root/clawd/memory/knowledge/writing-styles/xxx.md

# 4. 更新索引
/root/clawd/memory/knowledge/KNOWLEDGE_INDEX.md

# 5. 如果是核心知识，提炼到MEMORY.md
```

---

## 知识使用规则

### 创作任务

```
1. 读 KNOWLEDGE_INDEX.md
2. 加载 writing-styles/ 所有文件
3. 加载 product-knowledge/ 相关文件
4. 开始创作（参考风格+内容）
```

### 问答任务

```
1. 读 KNOWLEDGE_INDEX.md
2. 判断问题类型（技术/产品/商业）
3. 加载相关知识文件
4. 回答问题
```

### 新session启动

```
1. 读 SOUL.md（身份）
2. 读 MEMORY.md（核心记忆）
3. 读 NOW.md（当前状态）
4. 读 KNOWLEDGE_INDEX.md（知识目录）
5. 根据pending任务，加载相关知识
```

---

## 知识维护

### 定期清理

- 每月检查一次
- >30天未引用的知识 → 标记 `[⚠️ STALE]`
- 过期知识 → 移至 `.archive/`

### 版本控制

- 所有知识文件纳入Git
- 修改有记录
- 可回溯

---

## 当前行动项

1. **创建目录结构**
   ```bash
   mkdir -p /root/clawd/memory/knowledge/{writing-styles,tutorials,product-knowledge,business,technical,feedback}
   ```

2. **迁移现有知识**
   - 已有：`writing-styles/openclaw-爆款文章-onehopeA9.md`
   - 待迁移：lessons/decisions中可复用的内容

3. **创建索引**
   - `KNOWLEDGE_INDEX.md`

4. **更新AGENTS.md**
   - 添加知识库使用规则

---

**需要你确认**：
1. 这个方案可行吗？
2. 知识分类是否合理？
3. 要不要现在就开始实施？
