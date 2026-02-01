---
name: web3-dev
description: Web3开发助手，专门用于区块链脚本开发、撸毛项目自动化和加密货币交易。支持以太坊、BSC、Polygon等主流链的交互，包括代币查询、价格监控、批量操作、DeFi协议交互等功能。
---

# Web3开发助手

专为Web3开发者设计的综合工具包，涵盖脚本开发、撸毛自动化和交易辅助。

## 核心功能

### 1. 脚本开发
- 智能合约交互脚本
- 批量钱包操作
- 交易监控和自动化
- Gas费优化策略

### 2. 撸毛项目
- 项目信息收集和分析
- 批量账户管理
- 自动化交互脚本
- 收益统计和跟踪

### 3. 交易辅助
- 实时价格监控
- 技术分析指标
- 交易信号生成
- 风险管理工具

## 支持的区块链

- **以太坊 (Ethereum)**
- **币安智能链 (BSC)**
- **Polygon**
- **Arbitrum**
- **Optimism**
- **Avalanche**

## 常用工具

### 价格查询
使用 `scripts/price_check.py` 查询代币价格和市场数据。

### 批量操作
使用 `scripts/batch_operations.py` 进行批量转账、授权等操作。

### Gas监控
使用 `scripts/gas_tracker.py` 监控各链Gas费用。

## 参考资料

- **DeFi协议**: 查看 `references/defi_protocols.md` 了解主流DeFi协议接口
- **撸毛策略**: 查看 `references/airdrop_strategies.md` 了解撸毛项目分析方法
- **交易策略**: 查看 `references/trading_strategies.md` 了解常用交易策略

## 安全提醒

- 永远不要在代码中硬编码私钥
- 使用环境变量管理敏感信息
- 在主网操作前先在测试网验证
- 设置合理的滑点和Gas限制