#!/usr/bin/env python3
"""
电商价格对比工具 - 使用 Playwright
"""
from playwright.sync_api import sync_playwright
import time

def search_jd(query):
    """京东搜索"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f'https://search.jd.com/Search?keyword={query}', timeout=30000)
            page.wait_for_selector('.gl-item', timeout=10000)
            
            items = page.query_selector_all('.gl-item')[:3]
            results = []
            
            for item in items:
                try:
                    title_elem = item.query_selector('.p-name a em')
                    price_elem = item.query_selector('.p-price .J-p')
                    
                    title = title_elem.inner_text() if title_elem else 'N/A'
                    price = price_elem.inner_text() if price_elem else 'N/A'
                    
                    results.append({'title': title, 'price': price})
                except:
                    pass
            
            return results
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            browser.close()

def search_taobao(query):
    """淘宝搜索"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f'https://s.taobao.com/search?q={query}', timeout=30000)
            time.sleep(3)  # 等待页面加载
            
            # 淘宝的价格选择器可能不同
            items = page.query_selector_all('.Card--doubleCardWrapper--L2XFE73')[:3]
            results = []
            
            for item in items:
                try:
                    title_elem = item.query_selector('.Title--title--jCYPvpf')
                    price_elem = item.query_selector('.Price--priceInt--ZS9NZZC')
                    
                    title = title_elem.inner_text() if title_elem else 'N/A'
                    price = price_elem.inner_text() if price_elem else 'N/A'
                    
                    results.append({'title': title, 'price': price})
                except:
                    pass
            
            return results if results else "未找到商品"
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            browser.close()

def search_pdd(query):
    """拼多多搜索"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f'https://search.pinduoduo.com/search?keyword={query}', timeout=30000)
            time.sleep(3)
            
            items = page.query_selector_all('.goods-item')[:3]
            results = []
            
            for item in items:
                try:
                    title_elem = item.query_selector('.goods-title')
                    price_elem = item.query_selector('.goods-price')
                    
                    title = title_elem.inner_text() if title_elem else 'N/A'
                    price = price_elem.inner_text() if price_elem else 'N/A'
                    
                    results.append({'title': title, 'price': price})
                except:
                    pass
            
            return results if results else "未找到商品"
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            browser.close()

if __name__ == '__main__':
    product = "Logitech G715 机械键盘"
    
    print("=" * 60)
    print(f"正在搜索: {product}")
    print("=" * 60)
    
    print("\n【京东】")
    jd_results = search_jd(product)
    print(jd_results)
    
    print("\n【淘宝】")
    tb_results = search_taobao(product)
    print(tb_results)
    
    print("\n【拼多多】")
    pdd_results = search_pdd(product)
    print(pdd_results)
