#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书自动化客户端
使用 Cookie 登录，支持发布笔记、搜索等功能
"""

import requests
import json
import time
import random
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class XHSCookie:
    """小红书 Cookie"""
    web_session: str
    id_token: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "web_session": self.web_session,
            "id_token": self.id_token
        }

    def to_cookie_string(self) -> str:
        return f"web_session={self.web_session}; id_token={self.id_token}"


class XHSClient:
    """小红书客户端"""

    def __init__(self, cookie: XHSCookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Origin": "https://www.xiaohongshu.com",
            "Referer": "https://www.xiaohongshu.com/",
        })
        self.session.cookies.update(self.cookie.to_dict())

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = self.session.headers.copy()
        headers["Cookie"] = self.cookie.to_cookie_string()
        return headers

    def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            url = "https://edith.xiaohongshu.com/api/sns/web/v1/user/selfinfo/"
            response = self.session.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    user_info = data.get("data", {})
                    print(f"✅ 登录成功！用户: {user_info.get('nickname', '未知')}")
                    print(f"   粉丝数: {user_info.get('follows', 0)} | 关注数: {user_info.get('fans', 0)}")
                    return True

            print(f"❌ 登录失败，状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

        except Exception as e:
            print(f"❌ 检查登录状态时出错: {e}")
            return False

    def publish_note(
        self,
        title: str,
        content: str,
        images: List[str],
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        发布小红书笔记

        Args:
            title: 标题（最多20个字）
            content: 正文内容
            images: 图片列表（本地路径或URL）
            tags: 话题标签列表

        Returns:
            是否发布成功
        """
        try:
            # TODO: 实现发布逻辑
            print(f"准备发布笔记:")
            print(f"  标题: {title}")
            print(f"  内容: {content[:50]}...")
            print(f"  图片数: {len(images)}")
            print(f"  标签: {tags or []}")

            # 这里需要调用小红书的发布 API
            # API 接口需要逆向分析
            print("⚠️ 发布功能需要进一步开发 API 接口")
            return False

        except Exception as e:
            print(f"❌ 发布笔记时出错: {e}")
            return False

    def search_notes(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索小红书笔记

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量

        Returns:
            笔记列表
        """
        try:
            url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
            params = {
                "keyword": keyword,
                "page": 1,
                "page_size": limit
            }

            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    items = data.get("data", {}).get("items", [])
                    print(f"✅ 搜索到 {len(items)} 条笔记")
                    return items

            print(f"❌ 搜索失败，状态码: {response.status_code}")
            return []

        except Exception as e:
            print(f"❌ 搜索时出错: {e}")
            return []


def main():
    """测试函数"""
    # 使用爸爸提供的 Cookie
    cookie = XHSCookie(
        web_session="0400698cb54111563199c33cab3b4b74dc2dca",
        id_token="VjEAAI7z0bo813hs626Ib1e7l5vsaRC/k+XIYzEnIE2pCF5XSnRiWtUB3cLvva8YxodustIdf1pVsEaVLOTgNqscVgIysNA66lXFdo5q2cVkvJvHxwm+l0j1/yzjerW2Sj2WCRfD"
    )

    # 创建客户端
    client = XHSClient(cookie)

    # 测试登录状态
    print("=" * 50)
    print("测试小红书客户端")
    print("=" * 50)
    client.check_login_status()

    # 测试搜索
    print("\n" + "=" * 50)
    print("测试搜索功能")
    print("=" * 50)
    results = client.search_notes("美食", limit=5)
    if results:
        for i, note in enumerate(results[:3], 1):
            print(f"\n笔记 {i}:")
            print(f"  标题: {note.get('note_card', {}).get('title', '未知')}")


if __name__ == "__main__":
    main()
