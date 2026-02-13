#!/usr/bin/env python3
import ccxt
import asyncio
import ccxt.async_support as ccxt_async
import time
from datetime import datetime

# 测试的交易所列表
EXCHANGES_TO_TEST = [
    'binance',
    'bybit',
    'bitget',
    'okx',
    'huobi',
    'gate',
    'kucoin',
    'coinbase',
    'kraken',
    'bingx',
    'mexc'
]

def test_exchange_sync(exchange_id):
    """同步测试单个交易所"""
    print(f"\n🔍 测试 {exchange_id.upper()} (同步)...", end=' ')
    try:
        ex_class = getattr(ccxt, exchange_id)
        exchange = ex_class({
            'enableRateLimit': True,
            'timeout': 10000,
            'options': {'defaultType': 'future'} if exchange_id in ['binance', 'bybit', 'bitget'] else {}
        })

        # 测试1: 加载市场
        start = time.time()
        markets = exchange.load_markets()
        load_time = time.time() - start

        # 测试2: 获取ticker
        ticker = exchange.fetch_ticker('BTC/USDT')

        # 测试3: 获取K线
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=10)

        print(f"✅ 可用 (加载市场: {load_time:.2f}s)")
        print(f"   - 市场数量: {len(markets)}")
        print(f"   - BTC价格: {ticker['last']}")
        print(f"   - K线数据: {len(ohlcv)} 条")

        exchange.close()
        return {'id': exchange_id, 'status': 'success', 'load_time': load_time}

    except Exception as e:
        error_msg = str(e)
        if 'restricted' in error_msg.lower() or 'unavailable' in error_msg.lower():
            print(f"❌ 地区限制")
        elif 'timeout' in error_msg.lower():
            print(f"❌ 超时")
        elif '403' in error_msg or '401' in error_msg:
            print(f"❌ 访问被拒绝")
        else:
            print(f"❌ 错误: {type(e).__name__}")
        print(f"   详情: {error_msg[:100]}")

        return {'id': exchange_id, 'status': 'failed', 'error': error_msg[:100]}

async def test_exchange_async(exchange_id):
    """异步测试单个交易所"""
    print(f"\n🔍 测试 {exchange_id.upper()} (异步)...", end=' ')
    try:
        ex_class = getattr(ccxt_async, exchange_id)
        exchange = ex_class({
            'enableRateLimit': True,
            'timeout': 10000,
            'options': {'defaultType': 'future'} if exchange_id in ['binance', 'bybit', 'bitget'] else {}
        })

        # 测试1: 加载市场
        start = time.time()
        markets = await exchange.load_markets()
        load_time = time.time() - start

        # 测试2: 获取ticker
        ticker = await exchange.fetch_ticker('BTC/USDT')

        # 测试3: 获取K线
        ohlcv = await exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=10)

        print(f"✅ 可用 (加载市场: {load_time:.2f}s)")
        print(f"   - 市场数量: {len(markets)}")
        print(f"   - BTC价格: {ticker['last']}")

        await exchange.close()
        return {'id': exchange_id, 'status': 'success', 'load_time': load_time, 'mode': 'async'}

    except Exception as e:
        error_msg = str(e)
        if 'restricted' in error_msg.lower() or 'unavailable' in error_msg.lower():
            print(f"❌ 地区限制")
        elif 'timeout' in error_msg.lower():
            print(f"❌ 超时")
        elif '403' in error_msg or '401' in error_msg:
            print(f"❌ 访问被拒绝")
        else:
            print(f"❌ 错误: {type(e).__name__}")
        print(f"   详情: {error_msg[:100]}")

        await exchange.close()
        return {'id': exchange_id, 'status': 'failed', 'error': error_msg[:100], 'mode': 'async'}

def run_sync_tests():
    """运行同步测试"""
    print("\n" + "="*60)
    print("📡 开始同步测试交易所可用性")
    print("="*60)

    results = []
    for exchange_id in EXCHANGES_TO_TEST:
        if not hasattr(ccxt, exchange_id):
            print(f"\n⏭️  {exchange_id.upper()}: CCXT 不支持")
            continue

        result = test_exchange_sync(exchange_id)
        results.append(result)
        time.sleep(1)  # 避免触发限流

    return results

async def run_async_tests():
    """运行异步测试"""
    print("\n" + "="*60)
    print("📡 开始异步测试交易所可用性")
    print("="*60)

    tasks = []
    for exchange_id in EXCHANGES_TO_TEST:
        if not hasattr(ccxt_async, exchange_id):
            print(f"\n⏭️  {exchange_id.upper()}: CCXT 不支持")
            continue

        tasks.append(test_exchange_async(exchange_id))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if r]

def print_summary(results):
    """打印测试结果摘要"""
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    successful = [r for r in results if r.get('status') == 'success']
    failed = [r for r in results if r.get('status') != 'success']

    print(f"\n✅ 可用 ({len(successful)}):")
    for r in sorted(successful, key=lambda x: x.get('load_time', 999)):
        mode = r.get('mode', 'sync')
        print(f"   - {r['id'].upper():<10} (加载: {r.get('load_time', 0):.2f}s, 模式: {mode})")

    print(f"\n❌ 不可用 ({len(failed)}):")
    for r in failed:
        print(f"   - {r['id'].upper():<10} ({r.get('error', '未知错误')})")

    if successful:
        print(f"\n💡 推荐配置 (按速度排序):")
        print(f"EXCHANGES_TO_LOAD = {{")
        for i, r in enumerate(sorted(successful, key=lambda x: x.get('load_time', 999))):
            comma = "," if i < len(successful) - 1 else ""
            ex_id = r['id']
            options = "{{'defaultType': 'future'}}" if ex_id in ['binance', 'bybit', 'bitget'] else "{}"
            print(f"    '{ex_id}': {{'enableRateLimit': True, 'options': {options}, 'timeout': 30000}}{comma}")
        print(f"}}")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("🚀 交易所可用性测试脚本")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 同步测试
    sync_results = run_sync_tests()
    print_summary(sync_results)

    # 异步测试
    print("\n\n" + "="*60)
    async_results = asyncio.run(run_async_tests())
    print_summary(async_results)

    print(f"\n{'='*60}")
    print("✅ 测试完成")
    print(f"{'='*60}\n")
