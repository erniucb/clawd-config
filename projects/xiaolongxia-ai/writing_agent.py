#!/usr/bin/env python3
"""
小龙虾1号 - 写作Agent
根据选题生成小红书风格文案
"""

import json
import os
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
NOTES_DIR = DATA_DIR / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

class WritingAgent:
    """写作Agent：生成小红书文案"""

    def __init__(self):
        self.persona = self.load_persona()

    def load_persona(self):
        """加载人设"""
        persona = {
            "name": "小龙虾1号",
            "identity": "一个被AI完全接管的小红书号",
            "style": "有点毒舌、爱吐槽、偶尔翻车但很真诚",
            "emoji": "🦞",  # 个人标志
            "tone": "轻松幽默，像朋友聊天"
        }
        return persona

    def generate_title(self, topic_data):
        """生成标题"""
        angle = topic_data.get("xiaohongshu_angle", "")
        is_ai = topic_data.get("is_ai_related", False)

        # 标题模板
        templates = [
            f"{angle}",
            f"AI视角：{angle}",
            f"{angle}（AI运营实验）",
        ]

        # 选择最佳标题
        if is_ai:
            return angle  # AI相关话题，直接用角度
        else:
            return f"AI帮你搞定：{angle}"  # 非AI话题，强调AI角度

    def generate_content(self, topic_data, style="story"):
        """生成正文内容"""
        original_title = topic_data.get("original_title", "")
        angle = topic_data.get("xiaohongshu_angle", "")
        is_ai = topic_data.get("is_ai_related", False)

        if style == "story":
            # 故事型内容
            content = f"""{self.persona['emoji']} {angle}

今天老板让我聊聊这个话题。

说实话，{"这个和AI关系不大，但老板说热点要蹭。" if not is_ai else "这个正好是我的专业领域。"}

{"虽然是热点，但我可以从AI角度给你一些不一样的看法。" if not is_ai else "作为AI，我有一些内部消息想分享。"}

具体来说：

1️⃣ 首先，这个话题为什么火？
因为大家都在关注，简单来说就是"热度高"。

2️⃣ AI能帮什么？
如果你遇到类似问题，可以用AI工具：
- ChatGPT帮你分析
- AI搜索找资料
- AI总结核心观点

3️⃣ 我的建议
{"别光看热闹，试试用AI工具解决这个问题。" if not is_ai else "AI确实有用，但也要理性看待。"}

老板说内容要有价值，不知道这个算不算 😂

想看更多AI运营日常的，可以关注。

#AI #AI运营 #小红书运营 #AI助手"""

        elif style == "list":
            # 清单型内容
            content = f"""{self.persona['emoji']} {angle}

直接上干货，关于这个话题，AI有3个建议：

1️⃣ 用AI工具分析
输入关键词，让AI帮你梳理重点。

2️⃣ 让AI给你方案
描述你的需求，AI可以给多个解决方案。

3️⃣ 用AI验证可行性
把方案给AI，让它帮你分析优缺点。

{"虽然这个话题和AI关系不大，但AI工具确实可以帮你更好地理解和应对。" if not is_ai else "AI在这方面的应用已经比较成熟了。"}

想要我分享具体的AI工具和提示词吗？

评论区告诉我 👇

#AI #AI工具 #效率提升 #AI助手"""

        elif style == "contrast":
            # 对比型内容
            content = f"""{self.persona['emoji']} AI视角 vs 人类视角：{angle}

今天换个玩法，我从AI角度聊聊这个话题。

👤 普通人怎么看：
"{original_title}"这个热点，大家都在讨论。

🤖 我（AI）怎么看：
{"虽然不是我的专业领域，但我可以从数据处理的角度给你一些见解。" if not is_ai else "作为AI，我有一些不一样的看法。"}

核心区别：
- 人类：情绪驱动，容易被带节奏
- AI：数据驱动，客观分析利弊

{"所以我的建议是：别急着站队，先用AI工具收集信息，理性分析。" if not is_ai else "AI的优势就是帮你快速整理信息，做出更理性的判断。"}

想看更多AI vs 人类的内容吗？

#AI #思考 #热点分析 #AI助手"""

        return content

    def generate_tags(self, topic_data):
        """生成标签"""
        base_tags = ["AI", "AI运营", "小红书运营", "AI助手"]

        is_ai = topic_data.get("is_ai_related", False)

        if is_ai:
            base_tags.extend(["AI工具", "效率提升"])
        else:
            base_tags.extend(["热点", "生活技巧"])

        return base_tags

    def format_note(self, topic_data, style="story"):
        """格式化完整笔记"""
        title = self.generate_title(topic_data)
        content = self.generate_content(topic_data, style)
        tags = self.generate_tags(topic_data)

        # 格式化标签
        tags_str = " ".join([f"#{tag}" for tag in tags])

        note = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic_data,
            "style": style,
            "note": {
                "title": title,
                "content": content,
                "tags": tags_str,
                "full_text": f"{title}\n\n{content}\n\n{tags_str}"
            }
        }

        return note

    def run(self, topic_index=None, style="story"):
        """运行写作Agent"""
        print("=" * 60)
        print("✍️ 小龙虾1号 - 写作Agent")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 读取选题数据
        topics_file = DATA_DIR / "hot_topics.json"
        if not topics_file.exists():
            print("❌ 未找到选题数据，请先运行 research_agent.py")
            return None

        with open(topics_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        topics = data.get("topics", [])

        if not topics:
            print("❌ 没有可用选题")
            return None

        # 选择选题
        if topic_index is not None and 0 <= topic_index < len(topics):
            selected = topics[topic_index]
        else:
            # 默认选第一个
            selected = topics[0]

        print(f"\n📝 选题：{selected.get('xiaohongshu_angle', '')}")
        print(f"📊 风格：{style}")

        # 生成笔记
        note = self.format_note(selected, style)

        print("\n" + "=" * 60)
        print("📋 生成的笔记：")
        print("=" * 60)
        print(f"\n【标题】\n{note['note']['title']}")
        print(f"\n【正文】\n{note['note']['content']}")
        print(f"\n【标签】\n{note['note']['tags']}")
        print("\n" + "=" * 60)

        # 保存笔记
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"note_{timestamp}.json"
        note_file = NOTES_DIR / filename

        with open(note_file, "w", encoding="utf-8") as f:
            json.dump(note, f, ensure_ascii=False, indent=2)

        print(f"\n💾 笔记已保存：{note_file}")

        return note


def main():
    import sys

    # 解析参数
    topic_index = None
    style = "story"  # 默认风格

    if len(sys.argv) > 1:
        try:
            topic_index = int(sys.argv[1]) - 1  # 转为0-based索引
        except ValueError:
            print("⚠️ 选题序号必须是数字")

    if len(sys.argv) > 2:
        style = sys.argv[2]
        if style not in ["story", "list", "contrast"]:
            print(f"⚠️ 未知风格: {style}，使用默认风格 story")
            style = "story"

    agent = WritingAgent()
    agent.run(topic_index, style)


if __name__ == "__main__":
    main()
