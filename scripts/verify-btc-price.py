#!/usr/bin/env python3
import ccxt
import pandas as pd
from datetime import datetime

# 测试的交易所配置
EXCHANGES = {
    'okx': {
        'params': {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 10000},
        'symbol': 'BTC/USDT:USDT'  # OKX永续
    },
    'mexc': {
        'params': {'enableRateLimit': True, 'options': {'defaultType': 'future'}, 'timeout': 10000},
        'symbol': 'BTC/USDT'  # MEXC期货
    },
    'bitget': {
        'params': {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 10000},
        'symbol': 'BTC/USDT'  # Bitget永续
    },
    'gate': {
        'params': {'enableRateLimit': True, 'options': {'defaultType': 'futures'}, 'timeout': 10000},
        'symbol': 'BTC/USDT'  # Gate期货
    }
}

def get_price_info(ex_id, config):
    """从交易所获取详细的BTC价格信息"""
    print(f"\n{'='*70}")
    print(f"📡 {ex_id.upper()} - BTC/USDT 价格详情")
    print(f"{'='*70}")

    try:
        ex_class = getattr(ccxt, ex_id)
        exchange = ex_class(config['params'])

        # 1. 获取 ticker (实时报价)
        ticker = exchange.fetch_ticker(config['symbol'])
        print(f"📊 Ticker 数据:")
        print(f"   最新价: ${ticker['last']:,.2f}")
        print(f"   买一价: ${ticker['bid']:,.2f}")
        print(f"   卖一价: ${ticker['ask']:,.2f}")
        print(f"   24h最高: ${ticker['high']:,.2f}")
        print(f"   24h最低: ${ticker['low']:,.2f}")
        print(f"   24h成交量: {ticker['baseVolume']:,.4f} BTC")
        print(f"   24h成交额: ${ticker['quoteVolume']:,.2f} USDT")

        # 2. 获取最新K线 (1小时)
        ohlcv = exchange.fetch_ohlcv(config['symbol'], '1h', limit=5)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        print(f"\n📈 最新5根1小时K线:")
        print(f"   {'时间':<20} {'开盘':<12} {'最高':<12} {'最低':<12} {'收盘':<12} {'成交量'}")
        print(f"   {'-'*78}")
        for _, row in df.iterrows():
            print(f"   {row['timestamp'].strftime('%Y-%m-%d %H:%M'):<20} "
                  f"${row['open']:>10,.2f}  ${row['high']:>10,.2f}  "
                  f"${row['low']:>10,.2f}  ${row['close']:>10,.2f}  "
                  f"{row['volume']:>10.4f}")

        # 3. 获取订单簿 (显示买卖深度)
        orderbook = exchange.fetch_order_book(config['symbol'], limit=5)
        print(f"\n📋 订单簿 (前5档):")
        print(f"   卖盘:")
        for i, ask in enumerate(reversed(orderbook['asks'][:5])):
            price, amount = ask
            print(f"     {5-i}. ${price:,.2f} x {amount:.4f} BTC")

        print(f"   ------------------- ${ticker['last']:,.2f} (最新价)")
        print(f"   买盘:")
        for i, bid in enumerate(orderbook['bids'][:5]):
            price, amount = bid
            print(f"     {i+1}. ${price:,.2f} x {amount:.4f} BTC")

        # 4. 计算24小时涨跌幅
        change_pct = ((ticker['last'] - ticker['open']) / ticker['open']) * 100
        print(f"\n💹 24h涨跌: {change_pct:+.2f}%")

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 交易所BTC价格真实性验证")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("="*70)

    results = {}
    for ex_id, config in EXCHANGES.items():
        success = get_price_info(ex_id, config)
        results[ex_id] = success

    # 汇总对比
    print(f"\n{'='*70}")
    print("📊 价格汇总对比")
    print(f"{'='*70}")
    print(f"{'交易所':<12} {'最新价格':<15} {'24h最高':<15} {'24h最低':<15} {'状态'}")
    print(f"{'-'*70}")

    for ex_id, config in EXCHANGES.items():
        if results[ex_id]:
            try:
                ex_class = getattr(ccxt, ex_id)
                exchange = ex_class(config['params'])
                ticker = exchange.fetch_ticker(config['symbol'])
                print(f"{ex_id.upper():<12} ${ticker['last']:>11,.2f}   ${ticker['high']:>11,.2f}   "
                      f"${ticker['low']:>11,.2f}   ✅")
            except Exception as e:
                print(f"{ex_id.upper():<12} 数据错误   ❌")
        else:
            print(f"{ex_id.upper():<12} {'-'*13}   {'-'*13}   {'-'*13}   ❌")

    print(f"\n{'='*70}")
    print("✅ 测试完成 - 请对比各交易所价格是否合理")
    print(f"{'='*70}\n")
