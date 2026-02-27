# SKILLS_LIBRARY.md - 技能收藏库

收录Boss发现的有用技能、工具、最佳实践。

---

## 📌 使用方法

**添加新技能**：
- 在Twitter/GitHub/社区看到好用的技能
- 告诉贾维斯："收藏这个技能：[链接/描述]"
- 贾维斯会自动添加到下面

**技能格式**：
```markdown
### [技能名称]
- **来源**: Twitter/GitHub/社区
- **链接**: URL
- **功能**: 简要描述
- **安装**: 安装命令
- **状态**: 待安装/已安装/需要评估
- **备注**: 使用心得/注意事项
```

---

## 🔥 待安装技能

### 1. x-mcp 小红书浏览器插件版
- **来源**: xiaohongshu-mcp作者推荐
- **链接**: https://x.zouying.work/
- **功能**: 通过浏览器插件发小红书，无需服务器部署
- **安装**: Chrome商店安装 + API Token
- **状态**: 🔴 等待boss获取API Token
- **备注**: 比Docker版更适合非技术用户

### 2. 6551 开源新闻源 + Twitter MCP（强烈推荐！）✅
- **来源**: Twitter @cryptoxiao
- **链接**: 
  - GitHub: https://github.com/6551Team/opennews-mcp
  - GitHub: https://github.com/6551Team/opentwitter-mcp
  - ClawHub: https://clawhub.ai/infra403/opennews-mcp
  - ClawHub: https://clawhub.ai/infra403/opentwitter-mcp
- **功能**: 
  - ✅ 直连X数据 + 全网50+实时新闻源 + 链上数据
  - ✅ 无需配置API密钥（解决了X API难接的问题）
  - ✅ 24h监控、分析、触发Telegram提醒
  - ✅ 6551团队1年数据基础架构积累
  - ✅ Twitter用户信息、推文搜索、KOL跟踪
- **安装**: 
  ```bash
  cd /opt
  git clone https://github.com/6551Team/opennews-mcp.git
  git clone https://github.com/6551Team/opentwitter-mcp.git
  cp -r opennews-mcp/openclaw-skill/opennews ~/.openclaw/skills/
  cp -r opentwitter-mcp/openclaw-skill/opentwitter ~/.openclaw/skills/
  ```
- **状态**: ✅ 已安装已配置
- **配置**: Token已配置到 /opt/opennews-mcp/config.json 和 /opt/opentwitter-mcp/config.json
- **测试结果**: 
  - ✅ 新闻API：成功返回最新新闻（BTC/ETH/SOL等）
  - ✅ Twitter API：成功查询用户信息（elonmusk，2.35亿粉丝）
- **备注**: 
  - 解决了"新闻太多看不完"的问题
  - 解决了"X API难接 + Skill学不会"的痛点
  - Boss说"我们的X + 全网新闻源MCP + SKILL开源了"
  - API配额：9999次（剩余充足）

### 3. Ray Wang记忆管理架构（强烈推荐！）📚
- **来源**: Twitter @wangray
- **链接**: https://x.com/wangray/status/2027034737311907870
- **功能**: 
  - ✅ 三层记忆架构（短期NOW.md + 中期日志 + 长期知识库）
  - ✅ 自动温度衰减（30天无引用归档）
  - ✅ CRUD验证防止记忆幻觉
  - ✅ 夜间反思（23:45提炼+回写）
  - ✅ GC归档（每周日凌晨）
  - ✅ QMD语义搜索加速
  - ✅ 多Agent协作记忆
- **价值**: 
  - 基于5个Agent协作团队30天实际运行经验
  - 从"聊完就忘"到"结构化持久记忆"
  - 3000字完整实战指南
- **状态**: ✅ 已升级（阶段0完成）
- **下一步**:
  1. ✅ 创建 NOW.md（状态仪表盘）
  2. ✅ 创建 INDEX.md（知识导航）
  3. ✅ 创建 lessons/decisions/people/ 目录
  4. ⏳ 配置夜间反思cron（下周）
  5. ⏳ 实施GC归档机制（下周）
- **备注**: 
  - 这是目前看过最完整的OpenClaw记忆系统方案
  - 分阶段实施：阶段0→阶段1→阶段2→阶段3→阶段4
  - 不要一次性搭全，从最小3个文件开始

### 4. [技能名称]

---

## ✅ 已安装技能

### OpenClaw官方技能
- superpowers (12个开发技能)
- playwright-mcp (浏览器自动化)
- soroban-trader (Stellar DEX交易)
- base-trader (Base链交易)
- self-improving-agent (自我改进系统)

### 自建技能
- xiaohongshu-auto-publish (小红书发布 - Docker版)
  - 状态: ⚠️ 需要图形界面登录，暂停使用
  - 改用: x-mcp浏览器插件版

---

## 💡 技能最佳实践

### 发现渠道
- Twitter/X: #OpenClaw #AI助手
- GitHub: openclaw/openclaw discussions
- ClawHub: https://clawhub.com
- ClawStack: https://clawstack.sh

### 评估标准
1. 安全性：权限是否合理
2. 活跃度：最近更新时间
3. 社区反馈：Stars、Issues、讨论
4. 与现有技能冲突：避免重复

---

## 📅 更新记录

- 2026-02-26: 创建技能收藏库，添加x-mcp
