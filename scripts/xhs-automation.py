#!/usr/bin/env python3
"""
小红书自动化脚本
功能：
1. 每日定时搜索关键词
2. 收集热门笔记
3. 发布内容（需登录）
"""

import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/clawd/scripts/xhs_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class XiaohongshuAutomation:
    """小红书自动化类"""

    def __init__(self):
        self.npx_cmd = "npx -y @fastmcp-me/xhs-mcp"

    def check_login_status(self):
        """检查登录状态"""
        try:
            cmd = f"{self.npx_cmd} status"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            logger.info(f"登录状态检查: {result.stdout}")
            return "logged in" in result.stdout.lower()
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    def search_notes(self, keyword, limit=10):
        """搜索笔记"""
        try:
            cmd = f"{self.npx_cmd} search '{keyword}' --limit {limit}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            logger.info(f"搜索 '{keyword}' 完成")
            logger.info(f"结果: {result.stdout}")
            return result.stdout
        except Exception as e:
            logger.error(f"搜索笔记失败: {e}")
            return None

    def get_note_detail(self, note_id):
        """获取笔记详情"""
        try:
            cmd = f"{self.npx_cmd} note-detail --note-id {note_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            logger.info(f"获取笔记详情: {note_id}")
            return result.stdout
        except Exception as e:
            logger.error(f"获取笔记详情失败: {e}")
            return None

    def publish_note(self, title, content, image_paths=None):
        """发布笔记（需要登录）"""
        try:
            # 构建发布命令
            cmd = f"{self.npx_cmd} publish --title '{title}' --content '{content}'"
            if image_paths:
                cmd += f" --images {','.join(image_paths)}"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            logger.info(f"发布笔记: {title}")
            logger.info(f"结果: {result.stdout}")
            return result.returncode == 0
        except Exception as e:
            logger.error(f"发布笔记失败: {e}")
            return False

    def daily_search_task(self, keywords):
        """每日搜索任务"""
        logger.info("=" * 50)
        logger.info(f"开始每日搜索任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 检查登录状态
        if not self.check_login_status():
            logger.warning("未登录小红书，部分功能可能受限")
            logger.warning("请运行: npx -y @fastmcp-me/xhs-mcp login")

        # 搜索关键词
        results = {}
        for keyword in keywords:
            logger.info(f"\n搜索关键词: {keyword}")
            search_result = self.search_notes(keyword)
            results[keyword] = search_result

        # 保存结果
        output_dir = Path("/root/clawd/scripts/xhs_results")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"search_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n搜索结果已保存到: {output_file}")
        logger.info("=" * 50)

        return results

def main():
    """主函数"""
    automation = XiaohongshuAutomation()

    # 要搜索的关键词列表
    keywords = [
        "AI助手",
        "Web3",
        "加密货币",
        "技术分享",
        "OpenClaw"
    ]

    # 执行每日搜索任务
    results = automation.daily_search_task(keywords)

    # 打印摘要
    print("\n📊 搜索摘要:")
    for keyword, result in results.items():
        if result:
            print(f"  ✅ {keyword}: 已完成")
        else:
            print(f"  ❌ {keyword}: 失败")

if __name__ == "__main__":
    main()
