#!/usr/bin/env python3
"""
小红书热点扫描器
使用 Playwright 抓取小红书热门内容
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def scan_xiaohongshu():
    """扫描小红书热门"""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print("🌐 访问小红书...")
            await page.goto('https://www.xiaohongshu.com/explore', timeout=30000)
            await page.wait_for_timeout(3000)  # 等待JS渲染
            
            # 尝试获取热门笔记
            print("📊 提取热门内容...")
            
            # 滚动加载更多内容
            for _ in range(3):
                await page.evaluate('window.scrollBy(0, 1000)')
                await page.wait_for_timeout(1000)
            
            # 提取笔记信息
            notes = await page.evaluate('''
                () => {
                    const results = [];
                    // 尝试多种选择器
                    const selectors = [
                        'section.note-item',
                        '.note-item',
                        '[class*="noteItem"]',
                        'a[href*="/explore/"]'
                    ];
                    
                    for (const selector of selectors) {
                        const items = document.querySelectorAll(selector);
                        if (items.length > 0) {
                            items.forEach((item, index) => {
                                if (index < 20) {  // 最多20条
                                    const titleEl = item.querySelector('[class*="title"]') || 
                                                   item.querySelector('span') ||
                                                   item;
                                    const linkEl = item.querySelector('a') || item;
                                    const imgEl = item.querySelector('img');
                                    
                                    const title = titleEl ? titleEl.textContent.trim() : '';
                                    const link = linkEl ? linkEl.href : '';
                                    const img = imgEl ? imgEl.src : '';
                                    
                                    if (title || link) {
                                        results.push({
                                            title: title,
                                            link: link,
                                            image: img
                                        });
                                    }
                                }
                            });
                            break;
                        }
                    }
                    return results;
                }
            ''')
            
            if notes:
                results = notes
                print(f"✅ 找到 {len(notes)} 条内容")
            else:
                print("⚠️ 未找到笔记，尝试截图分析...")
                screenshot = await page.screenshot(type='jpeg', quality=80)
                results = [{
                    "type": "screenshot",
                    "message": "页面内容需要人工分析，已截图",
                    "screenshot_size": len(screenshot)
                }]
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            results = [{"error": str(e)}]
        finally:
            await browser.close()
    
    return results

async def main():
    """主函数"""
    print("=" * 50)
    print("🔴 小红书热点扫描器")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    results = await scan_xiaohongshu()
    
    print("\n📋 扫描结果:")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 保存结果
    output_file = '/root/clawd/scripts/xiaohongshu_hot.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存到: {output_file}")

if __name__ == '__main__':
    asyncio.run(main())
