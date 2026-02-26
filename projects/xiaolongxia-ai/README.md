# 🦞 小龙虾1号 - AI运营内容工厂

## 项目简介

小龙虾1号是一个由AI完全接管的小红书号，通过多Agent协作自动生产内容。

**核心卖点**：不是卖货号，是"AI运营实验"内容号。

---

## 快速开始

### 1. 运行完整流程（推荐）
```bash
cd /root/clawd/projects/xiaolongxia-ai
python3 xiaolongxia.py run
```

这会自动完成：
- ✅ 扫描热点（微博/小红书/AI新闻）
- ✅ 筛选选题
- ✅ 生成小红书文案
- ✅ 保存推送内容

### 2. 只运行研究Agent
```bash
python3 xiaolongxia.py research
```

### 3. 只运行写作Agent
```bash
# 使用第1个选题，故事风格
python3 xiaolongxia.py write --select 1 --style story

# 使用第2个选题，清单风格
python3 xiaolongxia.py write --select 2 --style list
```

### 4. 查看今日选题
```bash
python3 xiaolongxia.py topics
```

---

## 文件结构

```
xiaolongxia-ai/
├── PLAN.md              # 项目计划
├── PERSONA.md           # 小龙虾人设定义
├── README.md            # 本文档
├── xiaolongxia.py       # 主控制脚本
├── research_agent.py    # 研究Agent
├── writing_agent.py     # 写作Agent
└── data/
    ├── hot_topics.json      # 热点数据
    ├── telegram_push.txt    # 推送内容
    └── notes/               # 生成的笔记存档
        ├── note_20260225_093100.json
        └── ...
```

---

## 命令参数

### `xialongxia.py run`
完整流程：研究 → 写作 → 保存

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--select` | 选择第几个选题（1-3） | 1 |
| `--style` | 文案风格 | story |

**文案风格**：
- `story` - 故事型（推荐）
- `list` - 清单型
- `contrast` - 对比型

---

## 使用流程

### 日常运营流程

1. **早上9点**：运行研究Agent
   ```bash
   python3 xiaolongxia.py research
   ```

2. **查看选题**：选择要写的选题
   ```bash
   python3 xiaolongxia.py topics
   ```

3. **生成笔记**：根据选题生成文案
   ```bash
   # 选第2个选题，清单风格
   python3 xiaolongxia.py write --select 2 --style list
   ```

4. **审核发布**：
   - 查看 `data/telegram_push.txt`
   - 或查看 `data/notes/note_xxx.json`
   - 手动复制到小红书发布

---

## 自动化设置（可选）

### 定时任务
可以设置cron每天自动运行：

```bash
# 编辑crontab
crontab -e

# 每天早上9点运行
0 9 * * * cd /root/clawd/projects/xiaolongxia-ai && python3 xiaolongxia.py run
```

### Telegram自动推送
需要配置Telegram bot，将生成的内容自动推送到你的Telegram。

---

## 变现路径

1. **短期（1-3个月）**：提示词包销售
2. **中期（3-6个月）**：AI运营课程/工具推广
3. **长期（6个月+）**：矩阵号/社群

详见 `PLAN.md`

---

## 注意事项

### 平台风险控制
- ❌ 不频繁发营销内容
- ✅ 60%干货 + 30%互动 + 10%软广
- ❌ 避免敏感词（微信、加群、私信等）
- ✅ 发布环节人工操作

### 内容风险控制
- ✅ AI生成内容标注"AI创作"
- ❌ 避免虚假宣传
- ✅ 翻车也要诚实展示

---

## 更新日志

### 2026-02-25
- ✅ 创建项目结构
- ✅ 开发研究Agent
- ✅ 开发写作Agent
- ✅ 开发主控制脚本
- ✅ 完成第一次测试

---

## 下一步

1. **优化内容质量**：让生成的文案更自然
2. **增加内容类型**：增加更多文案模板
3. **集成Telegram推送**：自动推送到Telegram
4. **数据追踪**：记录笔记数据，优化选题

---

**项目创建时间**：2026-02-25
**维护者**：贾维斯 (AI助手)
