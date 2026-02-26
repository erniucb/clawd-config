# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config
**Statuses**: pending | in_progress | resolved | wont_fix | promoted | promoted_to_skill

## Status Definitions

| Status | Meaning |
|--------|---------|
| `pending` | Not yet addressed |
| `in_progress` | Actively being worked on |
| `resolved` | Issue fixed or knowledge integrated |
| `wont_fix` | Decided not to address (reason in Resolution) |
| `promoted` | Elevated to CLAUDE.md, AGENTS.md, or copilot-instructions.md |
| `promoted_to_skill` | Extracted as a reusable skill |

## Skill Extraction Fields

When a learning is promoted to a skill, add these fields:

```markdown
**Status**: promoted_to_skill
**Skill-Path**: skills/skill-name
```

Example:
```markdown
## [LRN-20250115-001] best_practice

**Logged**: 2025-01-15T10:00:00Z
**Priority**: high
**Status**: promoted_to_skill
**Skill-Path**: skills/docker-m1-fixes
**Area**: infra

### Summary
Docker build fails on Apple Silicon due to platform mismatch
...
```

---

## [LRN-20260225-001] best_practice

**Logged**: 2026-02-25T14:22:00Z
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
安装 self-improving-agent 技能用于持续学习和改进

### Details
从 ClawHub 安装了 self-improving-agent 技能。该技能用于记录学习、错误和功能请求，帮助 AI 助手持续改进。

安装步骤：
1. `git clone https://github.com/pskoett/self-improving-agent.git` 到 skills 目录
2. 创建 `.learnings/` 目录
3. 创建 LEARNINGS.md, ERRORS.md, FEATURE_REQUESTS.md

### Suggested Action
定期审查 .learnings 目录，将重要的学习记录晋升到 MEMORY.md 或相关技能文件中。

### Metadata
- Source: user_request
- Related Files: /root/clawd/skills/self-improving-agent/
- Tags: skill, learning, improvement

---

