#!/usr/bin/env python3
"""
Gas费监控工具
监控多条链的Gas费用情况
"""

import requests
import json
from typing import Dict, List

class GasTracker:
    def __init__(self):
        self.etherscan_api = "https://api.etherscan.io/api"
        self.bscscan_api = "https://api.bscscan.com/api"
        self.polygonscan_api = "https://api.polygonscan.com/api"
        
        # 需要设置API密钥
        self.api_keys = {
            "ethereum": "YOUR_ETHERSCAN_API_KEY",
            "bsc": "YOUR_BSCSCAN_API_KEY", 
            "polygon": "YOUR_POLYGONSCAN_API_KEY"
        }
    
    def get_ethereum_gas(self) -> Dict:
        """获取以太坊Gas费"""
        try:
            url = f"{self.etherscan_api}"
            params = {
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": self.api_keys["ethereum"]
            }
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"以太坊Gas查询错误: {e}")
            return {}
    
    def get_bsc_gas(self) -> Dict:
        """获取BSC Gas费"""
        try:
            url = f"{self.bscscan_api}"
            params = {
                "module": "gastracker",
                "action": "gasoracle",
                "apikey": self.api_keys["bsc"]
            }
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"BSC Gas查询错误: {e}")
            return {}
    
    def get_polygon_gas(self) -> Dict:
        """获取Polygon Gas费"""
        try:
            url = f"{self.polygonscan_api}"
            params = {
                "module": "gastracker", 
                "action": "gasoracle",
                "apikey": self.api_keys["polygon"]
            }
            response = requests.get(url, params=params)
            return response.json()
        except Exception as e:
            print(f"Polygon Gas查询错误: {e}")
            return {}
    
    def format_gas_info(self, gas_data: Dict, chain_name: str) -> str:
        """格式化Gas信息"""
        if not gas_data or gas_data.get("status") != "1":
            return f"{chain_name}: 无法获取Gas信息\n"
        
        result = gas_data.get("result", {})
        output = f"\n=== {chain_name} Gas费 ===\n"
        output += f"安全: {result.get('SafeGasPrice', 'N/A')} Gwei\n"
        output += f"标准: {result.get('ProposeGasPrice', 'N/A')} Gwei\n"
        output += f"快速: {result.get('FastGasPrice', 'N/A')} Gwei\n"
        
        return output
    
    def monitor_all_chains(self) -> str:
        """监控所有支持的链"""
        output = "=== 多链Gas费监控 ===\n"
        
        # 以太坊
        eth_gas = self.get_ethereum_gas()
        output += self.format_gas_info(eth_gas, "Ethereum")
        
        # BSC
        bsc_gas = self.get_bsc_gas()
        output += self.format_gas_info(bsc_gas, "BSC")
        
        # Polygon
        polygon_gas = self.get_polygon_gas()
        output += self.format_gas_info(polygon_gas, "Polygon")
        
        return output

def main():
    tracker = GasTracker()
    print(tracker.monitor_all_chains())

if __name__ == "__main__":
    main()