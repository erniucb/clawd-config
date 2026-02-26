#!/usr/bin/env python3
"""
记忆管理系统 - 三层架构
STM → LTM → Core Memory
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/clawd")
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
SOUL_FILE = WORKSPACE / "SOUL.md"
STATE_FILE = WORKSPACE / "memory_state.json"

# 配置
STM_DAYS = 8  # 短期记忆保留天数
IMPORTANCE_KEYWORDS = {
    "high": ["重要", "关键", "决定", "决策", "核心", "必须", "紧急", "风险", "错误", "问题", "升级", "成功", "完成", "解决", "配置", "安装"],
    "negative": ["不要", "避免", "禁止", "永远不", "never", "不能"],
    "medium": ["升级", "脚本", "版本", "命令", "路径", "邮箱"]
}

def load_state():
    """加载记忆状态"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "last_review": None,
        "promoted_items": [],
        "core_traits": []
    }

def save_state(state):
    """保存记忆状态"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def score_importance(content: str) -> float:
    """计算重要性评分 (0-1)"""
    score = 0.25  # 基础分
    
    # 高重要性关键词
    for kw in IMPORTANCE_KEYWORDS["high"]:
        if kw in content:
            score += 0.12
    
    # 负面/禁止关键词（这些往往是重要规则）
    for kw in IMPORTANCE_KEYWORDS["negative"]:
        if kw in content:
            score += 0.15
    
    # 中等重要性关键词
    for kw in IMPORTANCE_KEYWORDS.get("medium", []):
        if kw in content:
            score += 0.08
    
    # 长度因素
    if len(content) > 300:
        score += 0.1
    
    # 包含代码块或命令
    if '`' in content or '```' in content:
        score += 0.1
    
    return min(max(score, 0), 1.0)

def get_stm_files():
    """获取短期记忆文件"""
    if not MEMORY_DIR.exists():
        return []
    
    files = []
    cutoff = datetime.now() - timedelta(days=STM_DAYS)
    
    for f in MEMORY_DIR.glob("*.md"):
        try:
            date_str = f.stem  # YYYY-MM-DD
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date >= cutoff:
                files.append((f, file_date))
        except:
            continue
    
    return sorted(files, key=lambda x: x[1], reverse=True)

def extract_important_items(content: str, threshold: float = 0.5) -> list:
    """从内容中提取重要条目"""
    items = []
    
    # 按段落分割
    paragraphs = re.split(r'\n{2,}', content)
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        
        # 跳过纯标题行（只有#开头没有内容）
        if p.startswith('#') and '\n' not in p:
            continue
        
        score = score_importance(p)
        if score >= threshold:
            items.append({
                "content": p[:500],  # 截断
                "score": round(score, 2),
                "extracted_at": datetime.now().isoformat()
            })
    
    return items

def promote_to_ltm(items: list) -> int:
    """晋升到长期记忆"""
    if not items:
        return 0
    
    existing = ""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
    
    # 添加新条目
    new_section = "\n\n## 自动晋升记录\n\n"
    new_section += f"<!-- 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} -->\n\n"
    
    promoted = 0
    for item in items:
        # 检查是否已存在（简单去重）
        if item["content"][:100] in existing:
            continue
        
        new_section += f"### [重要性: {item['score']}] {datetime.now().strftime('%Y-%m-%d')}\n"
        new_section += f"{item['content']}\n\n"
        promoted += 1
    
    if promoted > 0:
        # 追加到 MEMORY.md
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(new_section)
    
    return promoted

def cleanup_stm():
    """清理过期的短期记忆"""
    if not MEMORY_DIR.exists():
        return 0
    
    cutoff = datetime.now() - timedelta(days=STM_DAYS)
    cleaned = 0
    
    for f in MEMORY_DIR.glob("*.md"):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                # 不删除，而是移动到 archive
                archive_dir = MEMORY_DIR / "archive"
                archive_dir.mkdir(exist_ok=True)
                f.rename(archive_dir / f.name)
                cleaned += 1
        except:
            continue
    
    return cleaned

def review_memory():
    """记忆审查 - 主入口"""
    state = load_state()
    state["last_review"] = datetime.now().isoformat()
    
    print("🧠 记忆系统审查开始...")
    print(f"   短期记忆保留期: {STM_DAYS} 天\n")
    
    # 1. 获取 STM 文件
    stm_files = get_stm_files()
    print(f"📂 当前短期记忆文件: {len(stm_files)} 个")
    
    # 2. 提取重要条目
    all_important = []
    for f, _ in stm_files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            items = extract_important_items(content)
            all_important.extend(items)
    
    print(f"🔍 发现重要条目: {len(all_important)} 个")
    
    # 3. 晋升到 LTM
    promoted = promote_to_ltm(all_important)
    print(f"⬆️  晋升到长期记忆: {promoted} 条")
    state["promoted_items"].extend([item["content"][:50] for item in all_important[:promoted]])
    
    # 4. 清理过期 STM
    cleaned = cleanup_stm()
    print(f"🗑️  归档过期记忆: {cleaned} 个文件")
    
    # 5. 保存状态
    save_state(state)
    
    print("\n✅ 记忆审查完成")
    print(f"   下次建议审查时间: {(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}")
    
    return {
        "stm_files": len(stm_files),
        "important_items": len(all_important),
        "promoted": promoted,
        "archived": cleaned
    }

def status():
    """显示记忆系统状态"""
    state = load_state()
    stm_files = get_stm_files()
    
    print("🧠 记忆系统状态\n")
    print(f"├── 短期记忆 (STM): {len(stm_files)} 个文件 (保留 {STM_DAYS} 天)")
    print(f"├── 长期记忆 (LTM): {MEMORY_FILE.name} ({'存在' if MEMORY_FILE.exists() else '不存在'})")
    print(f"├── 核心特质 (Core): {SOUL_FILE.name}")
    print(f"└── 上次审查: {state.get('last_review', '从未')}")
    
    if state.get("promoted_items"):
        print(f"\n最近晋升条目 ({len(state['promoted_items'])} 条):")
        for item in state["promoted_items"][-5:]:
            print(f"  • {item}...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "review":
            review_memory()
        elif cmd == "status":
            status()
        else:
            print(f"未知命令: {cmd}")
            print("用法: python memory_manager.py [review|status]")
    else:
        status()
