#!/usr/bin/env python3
"""
Twitter Web3热点追踪器
功能：
1. 扫描Twitter时间线，提取Web3相关推文
2. 识别新项目、空投信息、融资信息
3. 分析项目空投潜力
4. 每天中午12点定时发送报告
"""

import asyncio
import json
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class TwitterHotspotTracker:
    def __init__(self):
        self.data_file = Path('/root/clawd/data/twitter_hotspots.json')
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Web3关键词列表
        self.web3_keywords = {
            'airdrop': ['airdrop', '空投', 'whitelist', '白名单', 'claim', '领空'],
            'new_project': ['launch', 'launching', '首发', 'mainnet', '测试网', 'testnet', 'mainnet', 'v2'],
            'funding': ['funding', '融资', '投资', 'investment', 'round', '融资轮', 'a轮', 'b轮', 'seed', '种子轮'],
            'defi': ['defi', 'yield', '质押', 'restake', '流动性', 'mining', '挖矿'],
            'nft': ['nft', '白名单', 'wl', 'mint', '铸造', '发行', 'blindbox', '盲盒'],
            'token': ['token', '代币', 'coin', 'coinlist', '上所', '币安', 'okx', 'gate', 'binance'],
            'layer2': ['layer2', 'l2', 'rollup', 'zk', 'layer3', 'l3']
        }
        
        # 加载历史数据
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """加载历史数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'last_scan': None,
            'projects': {},
            'trends': {}
        }
    
    def _save_history(self):
        """保存历史数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def analyze_post(self, post: Dict) -> Dict:
        """分析推文并提取热点信息"""
        text = post.get('text', '').lower()
        author = post.get('author', '')
        url = post.get('url', '')
        
        result = {
            'text': post.get('text', ''),
            'author': author,
            'url': url,
            'time': post.get('time', ''),
            'categories': [],
            'project_name': None,
            'airdrop_info': None,
            'funding_info': None,
            'potential_score': 0
        }
        
        # 分类推文
        for category, keywords in self.web3_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    result['categories'].append(category)
        
        # 提取项目名称
        project_match = re.search(r'[\"\'『【]([a-zA-Z0-9]+)[\"\'』】]', text)
        if project_match:
            result['project_name'] = project_match.group(1)
        
        # 提取空投信息
        if 'airdrop' in result['categories']:
            airdrop_patterns = [
                r'白名单[:：\s*([a-zA-Z0-9]+)',
                r'claim\s*[:：]\s*([a-zA-Z0-9]+)',
                r'空投.*[:：]\s*([a-zA-Z0-9]+)'
            ]
            for pattern in airdrop_patterns:
                match = re.search(pattern, text)
                if match:
                    result['airdrop_info'] = match.group(1)
        
        # 提取融资信息
        if 'funding' in result['categories']:
            funding_match = re.search(r'([$]\s*[\d.,]+)\s*(万|million|billion)', text)
            if funding_match:
                result['funding_info'] = funding_match.group(1) + funding_match.group(2)
        
        # 计算潜力分数
        score = 0
        
        # 高潜力指标
        high_potential = [
            ('launch', 3), ('airdrop', 2), ('whitelist', 2), ('coinlist', 2)
        ]
        
        # 中潜力指标
        medium_potential = [
            ('funding', 2), ('testnet', 1), ('testnet测试网', 1)
        ]
        
        # 低潜力指标
        low_potential = [
            ('launching', 1), ('mainnet', 1), ('v2', 1)
        ]
        
        for category in result['categories']:
            if category in ['airdrop', 'new_project']:
                for keyword, points in high_potential:
                    if keyword in text:
                        score += points
            elif category in ['funding']:
                for keyword, points in medium_potential:
                    if keyword in text:
                        score += points
            else:
                for keyword, points in low_potential:
                    if keyword in text:
                        score += points
        
        # 项目活跃度加分
        activity_keywords = ['testnet', '测试网', '快照', 'snapshot', 'a1', 'a2', 'a3', 'alpha']
        if any(kw in text for kw in activity_keywords):
            score += 2
        
        # 官方账号加分
        official_keywords = ['official', '官方', 'team', '团队', 'dev', '开发']
        if any(kw in text for kw in official_keywords):
            score += 2
        
        result['potential_score'] = min(score, 10)
        
        return result
    
    async def scan_twitter(self) -> List[Dict]:
        """使用Playwright扫描Twitter"""
        print("正在扫描Twitter时间线...")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                'node',
                [
                    '-e',
                    f"""
const {{ chromium }} = require('playwright');

(async () => {{
  const context = await chromium.launchPersistentContext('/root/.config/google-chrome', {{
    headless: false,
    args: ['--disable-dev-shm-usage', '--no-sandbox']
  }});
  
  const page = await context.newPage();
  await page.goto('https://x.com/home', {{ waitUntil: 'domcontentloaded', timeout: 30000 }});
  await page.waitForTimeout(5000);
  
  // 滾动3次加载更多推文
  for (let i = 0; i < 3; i++) {{
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
  }}
  
  const posts = await page.evaluate(() => {{
    const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
    const results = [];
    
    for (let tweet of tweetElements) {{
      const textEl = tweet.querySelector('[data-testid="tweetText"]');
      const nameEl = tweet.querySelector('[data-testid="User-Name"]');
      const timeEl = tweet.querySelector('time');
      const linkEl = tweet.querySelector('a[href*="/status/"]');
      
      if (textEl && nameEl) {{
        const text = textEl.innerText;
        const author = nameEl.innerText;
        const url = linkEl ? 'https://x.com' + linkEl.getAttribute('href') : '';
        const time = timeEl ? timeEl.getAttribute('datetime') : '';
        
        results.push({{ text, author, url, time }});
      }}
    }}
    
    return results;
  }});
  
  console.log(JSON.stringify(posts));
  await context.close();
}})();
"""
                ],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc, timeout=120)
            
            if stdout:
                try:
                    # 从JSON中提取推文数据
                    json_start = stdout.find('[{')
                    json_end = stdout.rfind('}]') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        posts_str = stdout[json_start:json_end]
                        posts = json.loads(posts_str)
                        return posts
                except:
                    pass
            
            return []
            
        except asyncio.TimeoutError:
            print("扫描超时")
            return []
        except Exception as e:
            print(f"扫描错误: {e}")
            return []
    
    def analyze_posts(self, posts: List[Dict]) -> List[Dict]:
        """分析推文"""
        analyzed = []
        
        for post in posts:
            result = self.analyze_post(post)
            if result['potential_score'] >= 3:  # 只保留潜力>=3的
                analyzed.append(result)
        
        return analyzed
    
    def generate_report(self, analyzed_posts: List[Dict]) -> str:
        """生成报告"""
        if not analyzed_posts:
            return "今天没有发现高潜力的Web3热点"
        
        # 按潜力分数排序
        sorted_posts = sorted(analyzed_posts, key=lambda x: x['potential_score'], reverse=True)
        
        # 分类展示
        report = f"📊 Twitter Web3热点报告\\n"
        report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n"
        report += f"🎯 共发现 {len(analyzed_posts)} 个高潜力的Web3热点\\n\\n"
        
        # 高潜力热点 (分数7-10)
        high_potential = [p for p in sorted_posts if p['potential_score'] >= 7]
        if high_potential:
            report += "🔥🔥🔥 **高潜力热点** 🔥🔥🔥\\n"
            for i, post in enumerate(high_potential, 1):
                report += f"\\n{i}. {post['project_name'] or post['author']}\\n"
                report += f"   潜力: {post['potential_score']}/10\\n"
                report += f"   内容: {post['text'][:80]}...\\n"
        
        # 中潜力热点 (分数5-6)
        medium_potential = [p for p in sorted_posts if 5 <= p['potential_score'] <= 6]
        if medium_potential:
            report += "\\n⭐⭐⭐ **中潜力热点** ⭐⭐⭐\\n"
            for i, post in enumerate(medium_potential, 1):
                report += f"\\n{i}. {post['project_name'] or post['author']}\\n"
                report += f"   潜力: {post['potential_score']}/10\\n"
                report += f"   内容: {post['text'][:80]}...\\n"
        
        # 统计信息
        report += "\\n📊 **统计信息** 📊\\n"
        
        # 按类型统计
        category_count = {}
        for post in analyzed_posts:
            for cat in post['categories']:
                category_count[cat] = category_count.get(cat, 0) + 1
        
        report += f"空投相关: {category_count.get('airdrop', 0)}个\\n"
        report += f"新项目: {category_count.get('new_project', 0)}个\\n"
        report += f"融资信息: {category_count.get('funding', 0)}个\\n"
        
        return report
    
    async def scan_and_report(self):
        """扫描并发送报告"""
        print("\\n" + "="*50)
        print(f"开始扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*50 + "\\n")
        
        # 扫描Twitter
        posts = await self.scan_twitter()
        print(f"\\n扫描完成，获取到 {len(posts)} 条推文")
        
        # 分析推文
        analyzed = self.analyze_posts(posts)
        print(f"\\n分析完成，发现 {len(analyzed)} 个高潜力热点")
        
        # 生成报告
        report = self.generate_report(analyzed)
        print("\\n" + report)
        
        # 保存数据
        self.history['last_scan'] = datetime.now().isoformat()
        self.history['trends'][datetime.now().strftime('%Y-%m-%d')] = analyzed
        self._save_history()
        
        print("\\n✅ 数据已保存")
        print("等待明天中午12点自动发送...")

async def main():
    tracker = TwitterHotspotTracker()
    
    # 扫描并发送报告
    await tracker.scan_and_report()

if __name__ == "__main__":
    asyncio.run(main())
