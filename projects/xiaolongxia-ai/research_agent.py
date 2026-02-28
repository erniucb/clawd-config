#!/usr/bin/env python3
"""
小龙虾1号 - 研究Agent
扫描AI领域热点，筛选适合小红书的选题
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

class ResearchAgent:
    """研究Agent：扫描热点，生成选题"""

    def __init__(self):
        self.topics = []
        self.ai_keywords = [
            "AI", "人工智能", "ChatGPT", "GPT", "GPT-4", "GPT-5",
            "Claude", "Gemini", "文心一言", "通义千问", "Kimi",
            "AI绘画", "Midjourney", "Stable Diffusion", "DALL-E",
            "AI写作", "AI视频", "AI助手", "AI工具",
            "机器学习", "深度学习", "大模型", "LLM",
            "AI取代", "AI失业", "AI赚钱", "AI副业",
            "国产AI", "AI创业", "AI应用"
        ]

        # 排除词（太敏感或不适合小红书）
        self.exclude_keywords = [
            "政治", "习近平", "共产党", "台独", "藏独", "疆独",
            "色情", "赌博", "毒品", "暴力",
            "死亡", "自杀", "杀"
        ]

    async def scan_weibo_hot(self):
        """扫描微博热搜（通过 agent-reach 读取今日热榜）"""
        print("📱 扫描微博热搜...")

        import subprocess
        import re

        try:
            # 用 agent-reach 读取今日热榜微博页面
            result = subprocess.run(
                ["agent-reach", "read", "https://tophub.today/n/KqndgxeLl9"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"  ⚠️ agent-reach 执行失败")
                return []

            # 解析输出，提取热搜条目
            content = result.stdout
            weibo_hot = []

            # 匹配格式: 数字.[标题](链接)热度万
            # 例如: 1.[手机 涨价](https://...)117万
            pattern = r'(\d+)\.\[([^\]]+)\]\([^\)]+\)(\d+)万'
            matches = re.findall(pattern, content)

            for rank, title, heat_str in matches[:20]:  # 取前20条
                # 清理标题中的特殊字符
                title = title.strip()
                heat = int(heat_str) * 10000 if '万' in content else int(heat_str)

                weibo_hot.append({
                    "title": title,
                    "heat": heat,
                    "source": "weibo"
                })

            print(f"  ✅ 获取到 {len(weibo_hot)} 条微博热搜")
            return weibo_hot

        except Exception as e:
            print(f"  ⚠️ 微博热搜获取失败: {e}")
            return []

    async def scan_xiaohongshu_hot(self):
        """扫描小红书热门（复用已有脚本）"""
        print("🔴 扫描小红书热门...")

        try:
            # 调用已有的小红书扫描脚本
            import subprocess
            result = subprocess.run(
                ["python3", "/root/clawd/scripts/xiaohongshu_scanner.py"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # 读取结果
                with open("/root/clawd/scripts/xiaohongshu_hot.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("results", [])
            else:
                print(f"  ⚠️ 小红书扫描失败")
                return []
        except Exception as e:
            print(f"  ⚠️ 小红书扫描失败: {e}")
            return []

    async def scan_ai_news(self):
        """扫描AI新闻"""
        print("🤖 扫描AI新闻...")

        # 使用agent-reach搜索
        try:
            import subprocess
            result = subprocess.run(
                ["agent-reach", "search", "AI人工智能 最新新闻 2026"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # 解析搜索结果
                lines = result.stdout.strip().split("\n")
                news = []
                for line in lines[:10]:  # 前10条
                    if line.strip():
                        news.append({"title": line.strip(), "source": "agent-reach"})
                return news
            return []
        except Exception as e:
            print(f"  ⚠️ AI新闻获取失败: {e}")
            return []

    async def scan_x_twitter(self):
        """扫描X/Twitter上的AI热点（使用6551 opentwitter skill）"""
        print("🐦 扫描X/Twitter热点...")

        try:
            import os
            import requests

            # 优先从环境变量读取，否则从config.json读取
            twitter_token = os.getenv("TWITTER_TOKEN")
            
            if not twitter_token:
                # 从opentwitter-mcp的config.json读取
                config_path = "/opt/opentwitter-mcp/config.json"
                if os.path.exists(config_path):
                    import json
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        twitter_token = config.get("api_token", "")

            if not twitter_token:
                print(f"  ⚠️ TWITTER_TOKEN 未配置")
                return []

            # AI KOL账号列表（抓取他们的最新推文）
            ai_kols = [
                "elonmusk",  # 马斯克（经常提AI）
                "sama",      # Sam Altman (OpenAI CEO)
                "gdb",       # Greg Brockman (OpenAI)
                "karpathy",  # Andrej Karpathy (AI科学家)
            ]

            all_tweets = []
            headers = {
                "Authorization": f"Bearer {twitter_token}",
                "Content-Type": "application/json"
            }

            # 获取每个KOL的最新推文
            for username in ai_kols[:2]:  # 只取2个避免太慢
                url = "https://ai.6551.io/open/twitter_user_tweets"
                payload = {
                    "username": username,
                    "maxResults": 5,
                    "product": "Latest"
                }

                response = requests.post(url, headers=headers, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        for tweet in data["data"]:
                            text = tweet.get("text", "")
                            text = ' '.join(text.split()[:30])
                            if text and len(text) > 10:
                                heat = (tweet.get("favoriteCount", 0) or 0) + (tweet.get("retweetCount", 0) or 0)
                                all_tweets.append({
                                    "title": text,
                                    "source": "twitter",
                                    "heat": heat
                                })

            print(f"  ✅ 获取到 {len(all_tweets)} 条Twitter热点")
            return all_tweets

        except Exception as e:
            print(f"  ⚠️ Twitter热点获取失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def scan_zhihu_hot(self):
        """扫描知乎热榜"""
        print("📘 扫描知乎热榜...")

        try:
            import subprocess

            # 用agent-reach读取知乎热榜
            result = subprocess.run(
                ["agent-reach", "read", "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                zhihu_hot = []

                # 解析知乎热榜
                if isinstance(data, dict) and "data" in data:
                    for item in data["data"][:20]:
                        target = item.get("target", {})
                        title = target.get("title", "")
                        if title:
                            zhihu_hot.append({
                                "title": title,
                                "heat": item.get("detail_text", "").replace("热", "").replace("万", "0000"),
                                "source": "zhihu"
                            })

                print(f"  ✅ 获取到 {len(zhihu_hot)} 条知乎热榜")
                return zhihu_hot
            else:
                # 备用方案：读取知乎热榜页面
                result = subprocess.run(
                    ["agent-reach", "read", "https://www.zhihu.com/hot"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    import re
                    content = result.stdout
                    zhihu_hot = []

                    # 匹配知乎热榜标题
                    titles = re.findall(r'\d+\.\s+(.+?)(?:\n|\s{2,})', content)
                    for i, title in enumerate(titles[:20]):
                        title = title.strip()
                        if title and len(title) > 2:
                            zhihu_hot.append({
                                "title": title,
                                "source": "zhihu"
                            })

                    print(f"  ✅ 获取到 {len(zhihu_hot)} 条知乎热榜")
                    return zhihu_hot

            return []

        except Exception as e:
            print(f"  ⚠️ 知乎热榜获取失败: {e}")
            return []

    async def scan_36kr(self):
        """扫描36氪热点"""
        print("🚀 扫描36氪热点...")

        try:
            import subprocess

            # 用agent-reach读取36氪热榜
            result = subprocess.run(
                ["agent-reach", "read", "https://36kr.com/hot-list/catalog"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                import re
                content = result.stdout
                kr36_hot = []

                # 匹配36氪热榜标题
                # 格式通常是：数字. 标题
                lines = content.split('\n')
                for line in lines[:50]:
                    line = line.strip()
                    # 匹配标题格式
                    if re.match(r'^\d+\.', line):
                        title = re.sub(r'^\d+\.\s*', '', line)
                        title = title.strip()
                        if title and len(title) > 5:
                            kr36_hot.append({
                                "title": title,
                                "source": "36kr"
                            })

                print(f"  ✅ 获取到 {len(kr36_hot)} 条36氪热点")
                return kr36_hot
            else:
                # 备用方案：用搜索
                result = subprocess.run(
                    ["agent-reach", "search", "36氪 科技 创业 最新"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    kr36_hot = []
                    for line in lines[:10]:
                        if line.strip():
                            kr36_hot.append({
                                "title": line.strip(),
                                "source": "36kr"
                            })

                    print(f"  ✅ 获取到 {len(kr36_hot)} 条36氪热点")
                    return kr36_hot

            return []

        except Exception as e:
            print(f"  ⚠️ 36氪热点获取失败: {e}")
            return []

    def is_ai_related(self, title):
        """判断是否与AI相关"""
        title_upper = title.upper()
        return any(kw.upper() in title_upper for kw in self.ai_keywords)

    def is_sensitive(self, title):
        """判断是否包含敏感词"""
        return any(kw in title for kw in self.exclude_keywords)

    def filter_topics(self, raw_topics):
        """过滤选题"""
        filtered = []

        for topic in raw_topics:
            title = topic.get("title", "")

            # 排除敏感内容
            if self.is_sensitive(title):
                continue

            # 优先AI相关
            if self.is_ai_related(title):
                topic["ai_related"] = True
                topic["priority"] = 10
            else:
                topic["ai_related"] = False
                topic["priority"] = 5

            filtered.append(topic)

        # 按优先级和热度排序
        filtered.sort(key=lambda x: (x.get("priority", 0), x.get("heat", 0)), reverse=True)

        return filtered

    def generate_angle(self, topic):
        """生成小红书角度（更贴合平台调性）"""
        title = topic.get("title", "")
        heat = topic.get("heat", 0)

        # AI相关角度
        if topic.get("ai_related"):
            if "道歉" in title or "问题" in title or "翻车" in title:
                return "国产AI大模型翻车现场，AI也会犯错？"
            elif "新功能" in title or "发布" in title:
                return "AI新功能实测，真能提效？"
            elif "取代" in title or "失业" in title:
                return "AI要取代程序员？别慌，先看看这个"
            elif "赚钱" in title or "副业" in title:
                return "AI赚钱指南：普通人如何抓住机会"
            else:
                return f"🔥 AI圈大事件：{title[:20]}..."

        # 非AI话题，根据关键词生成小红书风格角度
        # 价格/消费相关
        if any(kw in title for kw in ["涨价", "价格", "贵", "便宜", "省钱"]):
            return f"💰 省钱攻略：{title[:15]}，这样买最划算！"

        # 科技/手机相关
        if any(kw in title for kw in ["手机", "苹果", "华为", "小米", "科技", "机器人"]):
            return f"📱 科技圈炸了！{title[:15]}..."

        # 娱乐/明星相关
        if any(kw in title for kw in ["明星", "演员", "歌手", "电影", "综艺", "恋爱", "结婚"]):
            return f"🌟 吃瓜！{title[:15]}..."

        # 社会热点
        if any(kw in title for kw in ["日本", "美国", "韩国", "争议", "回应"]):
            return f"🌏 热议：{title[:18]}..."

        # 经济/财经
        if any(kw in title for kw in ["经济", "市场", "万亿", "投资", "股市"]):
            return f"📈 财经热点：{title[:18]}..."

        # 美妆/时尚
        if any(kw in title for kw in ["穿搭", "化妆", "护肤", "衣服", "包包"]):
            return f"💄 变美秘籍：{title[:15]}..."

        # 健康/养生
        if any(kw in title for kw in ["健康", "养生", "减肥", "瘦", "病"]):
            return f"🏥 健康提醒：{title[:15]}..."

        # 高热度话题通用模板
        if heat > 500000:
            return f"🔥 全网热议！{title[:18]}..."

        # 默认模板
        return f"💡 热点速递：{title[:20]}..."

    def generate_reason(self, topic):
        """生成爆款理由"""
        reasons = []

        if topic.get("ai_related"):
            reasons.append("✅ AI热点自带流量")
        else:
            reasons.append("✅ 热门话题，已有热度")

        if topic.get("heat", 0) > 50000:
            reasons.append("✅ 高热度话题，曝光潜力大")

        reasons.append("✅ 可结合AI角度，差异化内容")

        return " | ".join(reasons)

    async def run(self):
        """运行研究Agent"""
        print("=" * 60)
        print("🦞 小龙虾1号 - 研究Agent")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        all_topics = []

        # 扫描各平台热点（暂时只启用验证可用的源）
        # weibo_topics = await self.scan_weibo_hot()  # 暂时禁用（agent-reach太慢）
        # all_topics.extend(weibo_topics)

        # xhs_topics = await self.scan_xiaohongshu_hot()  # 暂时禁用
        # for t in xhs_topics:
        #     if isinstance(t, dict) and t.get("title"):
        #         all_topics.append({"title": t["title"], "source": "xiaohongshu"})

        ai_news = await self.scan_ai_news()
        all_topics.extend(ai_news)

        # 新增：扫描X/Twitter（已验证可用）
        twitter_topics = await self.scan_x_twitter()
        all_topics.extend(twitter_topics)

        # 新增：扫描知乎热榜（暂时禁用，agent-reach太慢）
        # zhihu_topics = await self.scan_zhihu_hot()
        # all_topics.extend(zhihu_topics)

        # 新增：扫描36氪（暂时禁用）
        # kr36_topics = await self.scan_36kr()
        # all_topics.extend(kr36_topics)

        print(f"\n📊 共收集 {len(all_topics)} 条热点")

        # 过滤选题
        filtered = self.filter_topics(all_topics)
        print(f"✅ 过滤后 {len(filtered)} 条可用选题")

        # 生成TOP 3选题
        top3 = filtered[:3]

        result = {
            "timestamp": datetime.now().isoformat(),
            "total_collected": len(all_topics),
            "total_filtered": len(filtered),
            "topics": []
        }

        print("\n🎯 今日TOP 3选题：")
        print("-" * 60)

        for i, topic in enumerate(top3, 1):
            angle = self.generate_angle(topic)
            reason = self.generate_reason(topic)

            topic_data = {
                "rank": i,
                "original_title": topic.get("title", ""),
                "xiaohongshu_angle": angle,
                "explosion_reason": reason,
                "is_ai_related": topic.get("ai_related", False),
                "heat": topic.get("heat", 0),
                "source": topic.get("source", "unknown")
            }

            result["topics"].append(topic_data)

            print(f"\n#{i} {angle}")
            print(f"   原话题：{topic.get('title', '')}")
            print(f"   爆款理由：{reason}")
            print(f"   AI相关：{'✅' if topic.get('ai_related') else '❌'}")

        # 保存结果
        output_file = DATA_DIR / "hot_topics.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n💾 结果已保存：{output_file}")
        print("=" * 60)

        return result


async def main():
    agent = ResearchAgent()
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
