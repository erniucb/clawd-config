#!/usr/bin/env python3
import ccxt
import asyncio
import ccxt.async_support as ccxt_async

async def check_symbols():
    EXCHANGES = {
        'okx': {'options': {'defaultType': 'swap'}, 'timeout': 10000},
        'bitget': {'options': {'defaultType': 'swap'}, 'timeout': 10000},
        'mexc': {'options': {'defaultType': 'swap'}, 'timeout': 10000},
        'gate': {'options': {'defaultType': 'swap'}, 'timeout': 10000}
    }

    for ex_id, params in EXCHANGES.items():
        print(f"\n{'='*60}")
        print(f"📡 {ex_id.upper()} - 符号格式检查")
        print(f"{'='*60}")

        try:
            ex_class = getattr(ccxt_async, ex_id)
            exchange = ex_class({'enableRateLimit': True, **params})

            markets = await exchange.load_markets()

            # 找BTC相关的符号
            btc_symbols = [s for s in markets.keys() if 'BTC' in s and 'USDT' in s]
            print(f"\n找到 {len(btc_symbols)} 个BTC/USDT符号:")
            for sym in btc_symbols[:10]:  # 只显示前10个
                info = markets[sym]
                print(f"  - {sym}")
                print(f"    active: {info.get('active', False)}")
                print(f"    quoteVolume: {info.get('quoteVolume', 0):,.0f}")
                print(f"    type: {info.get('type', 'unknown')}")

            # 统计过滤后的数量
            usdt_swap = []
            for symbol, info in markets.items():
                if not (symbol.endswith(':USDT') or symbol.endswith('/USDT')):
                    continue
                if not info.get('active', True):
                    continue
                vol = info.get('quoteVolume', 0)
                if vol and vol > 3000000:
                    usdt_swap.append(symbol)

            print(f"\n过滤后 (>300万U): {len(usdt_swap)} 个")
            if usdt_swap:
                print("示例:")
                for sym in usdt_swap[:5]:
                    info = markets[sym]
                    print(f"  - {sym}: {info.get('quoteVolume', 0):,.0f} USDT")

            await exchange.close()

        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(check_symbols())
