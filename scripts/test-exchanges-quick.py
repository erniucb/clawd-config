#!/usr/bin/env python3
import ccxt
import time
from datetime import datetime

# 测试的交易所列表（先测主要的）
EXCHANGES_TO_TEST = [
    'binance',
    'bybit',
    'bitget',
    'okx',
    'gate',
    'mexc'
]

def test_exchange(exchange_id):
    """测试单个交易所"""
    print(f"🔍 测试 {exchange_id.upper()}...", end=' ', flush=True)
    try:
        ex_class = getattr(ccxt, exchange_id)
        exchange = ex_class({
            'enableRateLimit': True,
            'timeout': 8000,  # 8秒超时
            'options': {'defaultType': 'future'} if exchange_id in ['binance', 'bybit', 'bitget'] else {}
        })

        # 测试: 加载市场
        start = time.time()
        markets = exchange.load_markets()
        load_time = time.time() - start

        # 测试: 获取ticker
        ticker = exchange.fetch_ticker('BTC/USDT')

        print(f"✅ 可用 ({load_time:.1f}s) | BTC: ${ticker['last']:.2f}")

        exchange.close()
        return True

    except Exception as e:
        error_msg = str(e)
        if 'restricted' in error_msg.lower() or 'unavailable' in error_msg.lower():
            print(f"❌ 地区限制")
        elif 'timeout' in error_msg.lower():
            print(f"❌ 超时")
        elif '403' in error_msg:
            print(f"❌ 访问被拒绝")
        else:
            print(f"❌ {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 交易所可用性快速测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    working = []
    for exchange_id in EXCHANGES_TO_TEST:
        if not hasattr(ccxt, exchange_id):
            print(f"⏭️  {exchange_id.upper()}: CCXT 不支持\n")
            continue

        if test_exchange(exchange_id):
            working.append(exchange_id)
        print()
        time.sleep(1)  # 避免触发限流

    print("="*60)
    print("📊 结果汇总")
    print("="*60)
    if working:
        print(f"\n✅ 可用交易所 ({len(working)}):")
        for ex in working:
            print(f"   - {ex.upper()}")
    else:
        print(f"\n❌ 无可用交易所")

    print("\n" + "="*60 + "\n")
