#!/usr/bin/env python3
"""
代币价格查询工具
支持多个交易所和链的价格查询
"""

import requests
import json
from typing import Dict, Optional

class PriceChecker:
    def __init__(self):
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.dexscreener_api = "https://api.dexscreener.com/latest/dex"
    
    def get_token_price_coingecko(self, token_id: str, vs_currency: str = "usd") -> Optional[Dict]:
        """通过CoinGecko API查询代币价格"""
        try:
            url = f"{self.coingecko_api}/simple/price"
            params = {
                "ids": token_id,
                "vs_currencies": vs_currency,
                "include_24hr_change": "true",
                "include_market_cap": "true"
            }
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"CoinGecko API错误: {e}")
            return None
    
    def get_token_price_dexscreener(self, token_address: str, chain: str = "ethereum") -> Optional[Dict]:
        """通过DexScreener API查询代币价格"""
        try:
            url = f"{self.dexscreener_api}/tokens/{token_address}"
            response = requests.get(url)
            return response.json()
        except Exception as e:
            print(f"DexScreener API错误: {e}")
            return None
    
    def format_price_info(self, price_data: Dict, token_name: str = "") -> str:
        """格式化价格信息输出"""
        if not price_data:
            return "无法获取价格信息"
        
        output = f"\n=== {token_name} 价格信息 ===\n"
        
        # CoinGecko格式
        if isinstance(list(price_data.values())[0], dict):
            data = list(price_data.values())[0]
            output += f"价格: ${data.get('usd', 'N/A')}\n"
            output += f"24h变化: {data.get('usd_24h_change', 'N/A'):.2f}%\n"
            output += f"市值: ${data.get('usd_market_cap', 'N/A'):,}\n"
        
        return output

def main():
    checker = PriceChecker()
    
    # 示例查询
    print("查询ETH价格...")
    eth_price = checker.get_token_price_coingecko("ethereum")
    print(checker.format_price_info(eth_price, "Ethereum"))
    
    print("\n查询BTC价格...")
    btc_price = checker.get_token_price_coingecko("bitcoin")
    print(checker.format_price_info(btc_price, "Bitcoin"))

if __name__ == "__main__":
    main()