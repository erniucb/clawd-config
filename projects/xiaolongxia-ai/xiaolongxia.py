#!/usr/bin/env python3
"""
小龙虾1号 - 主控制脚本
一键运行：研究 → 写作 → 推送
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from research_agent import ResearchAgent
from writing_agent import WritingAgent


class XiaolongxiaController:
    """小龙虾1号主控制器"""

    def __init__(self):
        self.research_agent = ResearchAgent()
        self.writing_agent = WritingAgent()

    async def run_daily_workflow(self, auto_select=0, style="story"):
        """运行每日工作流"""
        print("\n" + "=" * 60)
        print("🦞 小龙虾1号 - 每日内容生产")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Step 1: 研究Agent - 扫描热点
        print("\n【步骤1】研究Agent - 扫描热点选题")
        print("-" * 60)
        research_result = await self.research_agent.run()

        if not research_result or not research_result.get("topics"):
            print("❌ 没有找到选题，流程结束")
            return None

        # Step 2: 写作Agent - 生成笔记
        print("\n【步骤2】写作Agent - 生成小红书笔记")
        print("-" * 60)
        note = self.writing_agent.run(topic_index=auto_select, style=style)

        if not note:
            print("❌ 笔记生成失败，流程结束")
            return None

        # Step 3: 汇总报告
        print("\n【步骤3】今日内容汇总")
        print("-" * 60)
        print(f"✅ 选题：{note['topic']['xiaohongshu_angle']}")
        print(f"✅ 风格：{note['style']}")
        print(f"✅ 笔记已保存")

        # 生成推送内容
        push_content = self.format_for_telegram(note)

        # 保存推送内容
        push_file = PROJECT_DIR / "data" / "telegram_push.txt"
        with open(push_file, "w", encoding="utf-8") as f:
            f.write(push_content)

        print(f"✅ 推送内容已保存：{push_file}")

        return {
            "research": research_result,
            "note": note,
            "push_content": push_content
        }

    def format_for_telegram(self, note):
        """格式化为Telegram推送格式"""
        topic = note['topic']
        note_content = note['note']

        push = f"""🦞 小龙虾1号 - 今日笔记

━━━━━━━━━━━━━━━━━━━━

📝 选题：{topic['xiaohongshu_angle']}
🔥 爆款理由：{topic['explosion_reason']}
🤖 AI相关：{'✅' if topic['is_ai_related'] else '❌'}

━━━━━━━━━━━━━━━━━━━━

【标题】
{note_content['title']}

【正文】
{note_content['content']}

【标签】
{note_content['tags']}

━━━━━━━━━━━━━━━━━━━━

⏰ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💬 审核后可手动发布到小红书
"""
        return push

    def show_today_topics(self):
        """显示今日选题"""
        topics_file = PROJECT_DIR / "data" / "hot_topics.json"

        if not topics_file.exists():
            print("❌ 未找到选题数据，请先运行研究Agent")
            return

        with open(topics_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        topics = data.get("topics", [])

        print("\n" + "=" * 60)
        print("🎯 今日选题列表")
        print("=" * 60)

        for i, topic in enumerate(topics, 1):
            print(f"\n#{i} {topic['xiaohongshu_angle']}")
            print(f"   原话题：{topic['original_title']}")
            print(f"   AI相关：{'✅' if topic['is_ai_related'] else '❌'}")

        print("\n" + "=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="小龙虾1号 - AI运营工具")
    parser.add_argument("command", choices=["run", "research", "write", "topics"],
                       help="命令：run=完整流程, research=只运行研究, write=只运行写作, topics=查看选题")
    parser.add_argument("--select", type=int, default=1,
                       help="选择第几个选题（1-3），默认1")
    parser.add_argument("--style", choices=["story", "list", "contrast"], default="story",
                       help="文案风格：story=故事型, list=清单型, contrast=对比型")

    args = parser.parse_args()

    controller = XiaolongxiaController()

    if args.command == "run":
        # 完整流程
        asyncio.run(controller.run_daily_workflow(
            auto_select=args.select - 1,
            style=args.style
        ))

    elif args.command == "research":
        # 只运行研究
        asyncio.run(controller.research_agent.run())

    elif args.command == "write":
        # 只运行写作
        controller.writing_agent.run(
            topic_index=args.select - 1,
            style=args.style
        )

    elif args.command == "topics":
        # 查看选题
        controller.show_today_topics()


if __name__ == "__main__":
    main()
