# DeFi协议接口参考

## Uniswap V2/V3
```python
# 价格查询
def get_token_price(token_address, router_address):
    # 通过路由器查询价格
    pass

# 交换代币
def swap_tokens(token_in, token_out, amount, slippage=0.5):
    # 执行代币交换
    pass
```

## PancakeSwap (BSC)
```python
# BSC上的DEX操作
PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
```

## Curve Finance
```python
# 稳定币交换
def curve_swap(pool_address, token_in, token_out, amount):
    pass
```

## Compound/AAVE
```python
# 借贷协议
def supply_token(token, amount):
    pass

def borrow_token(token, amount):
    pass
```

## 1inch聚合器
```python
# 获取最优交换路径
def get_best_swap_route(token_in, token_out, amount):
    pass
```