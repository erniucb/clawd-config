#!/usr/bin/env python3
"""
批量操作工具
支持批量转账、授权等Web3操作
"""

from web3 import Web3
from typing import List, Dict
import json
import time

class BatchOperations:
    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.address = self.account.address
    
    def batch_transfer_eth(self, recipients: List[Dict], gas_price: int = None) -> List[str]:
        """批量转账ETH"""
        tx_hashes = []
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        for recipient in recipients:
            try:
                tx = {
                    'to': recipient['address'],
                    'value': self.w3.to_wei(recipient['amount'], 'ether'),
                    'gas': 21000,
                    'gasPrice': gas_price or self.w3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': self.w3.eth.chain_id
                }
                
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hashes.append(tx_hash.hex())
                
                nonce += 1
                print(f"转账到 {recipient['address']}: {tx_hash.hex()}")
                
                # 避免nonce冲突
                time.sleep(1)
                
            except Exception as e:
                print(f"转账失败 {recipient['address']}: {e}")
        
        return tx_hashes
    
    def batch_approve_token(self, token_address: str, spenders: List[Dict]) -> List[str]:
        """批量授权代币"""
        # ERC20 ABI (简化版)
        erc20_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        contract = self.w3.eth.contract(address=token_address, abi=erc20_abi)
        tx_hashes = []
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        for spender in spenders:
            try:
                tx = contract.functions.approve(
                    spender['address'],
                    int(spender['amount'])
                ).build_transaction({
                    'from': self.address,
                    'gas': 60000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': nonce,
                    'chainId': self.w3.eth.chain_id
                })
                
                signed_tx = self.account.sign_transaction(tx)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                tx_hashes.append(tx_hash.hex())
                
                nonce += 1
                print(f"授权给 {spender['address']}: {tx_hash.hex()}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"授权失败 {spender['address']}: {e}")
        
        return tx_hashes
    
    def check_transaction_status(self, tx_hashes: List[str]) -> Dict:
        """检查交易状态"""
        results = {}
        
        for tx_hash in tx_hashes:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                results[tx_hash] = {
                    'status': 'success' if receipt.status == 1 else 'failed',
                    'gas_used': receipt.gasUsed,
                    'block_number': receipt.blockNumber
                }
            except Exception as e:
                results[tx_hash] = {'status': 'pending', 'error': str(e)}
        
        return results

def main():
    # 示例配置
    RPC_URL = "https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
    PRIVATE_KEY = "YOUR_PRIVATE_KEY"  # 注意：实际使用时从环境变量读取
    
    batch_ops = BatchOperations(RPC_URL, PRIVATE_KEY)
    
    # 批量转账示例
    recipients = [
        {'address': '0x...', 'amount': 0.01},
        {'address': '0x...', 'amount': 0.01}
    ]
    
    print("执行批量转账...")
    tx_hashes = batch_ops.batch_transfer_eth(recipients)
    
    # 检查交易状态
    print("\n检查交易状态...")
    status = batch_ops.check_transaction_status(tx_hashes)
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()