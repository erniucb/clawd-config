import ccxt
import pandas as pd
import numpy as np
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta

# ================= ⚙️ 用户配置区域 =================
# 1. 邮件设置
SENDER_EMAIL = '371398370@qq.com'
SENDER_PASSWORD = 'hjqibancxrerbifb'
RECEIVER_EMAIL = '371398370@qq.com'

# 2. 筛选设置
TIMEFRAME = '1h'       # 你的要求: 1小时线
LIMIT_COINS = 40       # 监控成交量前40的币 (范围稍微扩大一点)
MIN_HISTORY = 90       # 你的要求: 至少90根基础K线

# 3. 形态参数 (根据你的描述定制)
MAX_AMPLITUDE = 0.08   # 箱体最大振幅: 8% (5%略严, 8%较适中, 可自行修改)
TOUCH_THRESHOLD = 3    # 至少触碰 3 次边界
SQUEEZE_FACTOR = 0.7   # 末端收敛系数: 最后几根K线的波动 < 整体平均的 70%

# 4. 调度
CHECK_INTERVAL = 300   # 每5分钟扫描一次 (因为要抓"微微探头", 频率要高)

# ===========================================

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'},
    'timeout': 30000
})

# 用于记录已发送的报警，防止同一个突破重复发邮件
alert_cache = {} # 格式: {symbol: last_alert_time}

def send_email(symbol, price, box_high, box_low, amplitude, squeeze_msg):
    """发送突破报警"""
    direction = "向上突破 (做多)" if price > box_high else "向下跌破 (做空)"
    break_level = box_high if price > box_high else box_low

    subject = f"【结构突破】{symbol} 突破90周期箱体! ({direction})"

    content = f"""
    时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    币种: {symbol} (1H)
    ------------------------
    当前价格: {price}
    突破位置: {round(break_level, 4)}

    箱体结构分析:
    1. 震荡时长: {MIN_HISTORY} 小时
    2. 箱体幅度: {round(amplitude * 100, 2)}% (符合 < {MAX_AMPLITUDE*100}% 要求)
    3. 末端收敛: {squeeze_msg}

    战术建议:
    这是一次经过充分蓄势(90H+)的突破。
    当前价格刚刚探头，请立即查看图表确认成交量配合情况。
    止损建议: 箱体中轴或最近的收敛K线低点。
    """

    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr(["结构猎手", SENDER_EMAIL])
        msg['To'] = formataddr(["交易员", RECEIVER_EMAIL])
        msg['Subject'] = subject

        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功: {symbol}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def check_structure(df, symbol):
    """
    核心算法：识别【平缓箱体 + 多次触碰 + 末端收敛 + 突破】
    """
    # 1. 切片：取过去90根 (作为箱体基础)，不包含当前最新这根
    # df的最后一行是正在走的(current)，倒数第2行是刚收盘的
    # 我们用倒数 91 到 倒数 2 这一段来定义箱体
    box_data = df.iloc[-(MIN_HISTORY+1) : -1]
    current_candle = df.iloc[-1]

    if len(box_data) < MIN_HISTORY: return None

    # === A. 计算箱体幅度 ===
    highs = box_data['high']
    lows = box_data['low']
    box_high = highs.max()
    box_low = lows.min()

    # 计算幅度 (High - Low) / Low
    amplitude = (box_high - box_low) / box_low

    # 过滤1: 如果震荡幅度太大 (>8%)，或者太小(<1% 死鱼)，直接Pass
    if amplitude > MAX_AMPLITUDE or amplitude < 0.01:
        return None

    # === B. 验证触碰次数 (Loose Mode) ===
    # 定义 "边缘区": 价格在箱体上沿向下 15% 的空间内
    upper_zone = box_high - (box_high - box_low) * 0.15
    lower_zone = box_low + (box_high - box_low) * 0.15

    # 统计有多少根K线的高点打到了上沿区域
    touches_top = len(box_data[box_data['high'] > upper_zone])
    # 统计有多少根K线的低点打到了下沿区域
    touches_bottom = len(box_data[box_data['low'] < lower_zone])

    # 过滤2: 必须至少有一边触碰超过 3 次
    if touches_top < TOUCH_THRESHOLD and touches_bottom < TOUCH_THRESHOLD:
        return None

    # === C. 验证末端收敛 (The Squeeze) ===
    # 取箱体最后的 4 根 K 线
    last_4_candles = box_data.iloc[-4:]

    # 计算整体平均波动 (High - Low)
    avg_volatility = (box_data['high'] - box_data['low']).mean()
    # 计算最近4根的平均波动
    recent_volatility = (last_4_candles['high'] - last_4_candles['low']).mean()

    # 过滤3: 最近波动必须小于整体的 70% (变窄了)
    if recent_volatility > avg_volatility * SQUEEZE_FACTOR:
        return None # 波动没有收敛，还在剧烈震荡，Pass

    squeeze_msg = f"最近4小时波动率降低至 {round((recent_volatility/avg_volatility)*100)}%"

    # === D. 验证突破 (The Breakout) ===
    curr_price = current_candle['close'] # 这里的close在未收盘时就是最新价

    signal = None
    # 向上突破: 当前价 > 箱体最高价
    if curr_price > box_high:
        signal = "UP"
    # 向下跌破: 当前价 < 箱体最低价
    elif curr_price < box_low:
        signal = "DOWN"

    if signal:
        return {
            'signal': signal,
            'price': curr_price,
            'high': box_high,
            'low': box_low,
            'amp': amplitude,
            'msg': squeeze_msg
        }

    return None

def get_top_volume_coins():
    try:
        tickers = exchange.fetch_tickers()
        usdt_futures = [s for s, d in tickers.items() if '/USDT' in s and '24' not in s]
        # 按成交量排序，取前 Limit 个
        sorted_tickers = sorted(usdt_futures, key=lambda x: tickers[x]['quoteVolume'] if tickers[x]['quoteVolume'] else 0, reverse=True)
        return sorted_tickers[:LIMIT_COINS]
    except Exception as e:
        print(f"获取列表失败: {e}")
        return []

def run_scanner():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 开始扫描 90周期结构...")
    symbols = get_top_volume_coins()

    for symbol in symbols:
        try:
            # 多取一些数据，保证计算准确 (取120根)
            bars = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=120)
            if not bars: continue

            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # 核心识别
            result = check_structure(df, symbol)

            if result:
                # 检查冷却时间，防止一分钟发好几封邮件
                last_time = alert_cache.get(symbol)
                # 冷却时间设为 4小时 (同一个箱体突破只报一次)
                if last_time and datetime.now() - last_time < timedelta(hours=4):
                    continue

                print(f"🚀 发现结构突破: {symbol} Price:{result['price']}")

                if send_email(symbol, result['price'], result['high'], result['low'], result['amp'], result['msg']):
                    alert_cache[symbol] = datetime.now()

            time.sleep(0.1)
        except Exception as e:
            continue
    print("扫描完成.")

if __name__ == "__main__":
    print(f"🚀 结构猎手 V6.0 启动 (周期: {TIMEFRAME}, 箱体: {MIN_HISTORY})")
    while True:
        try:
            run_scanner()
            # 你的要求：微微探头就报警，所以不能等1小时。
            # 我们每 5 分钟扫一次，看最新价有没有捅破天花板。
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Main Error: {e}")
            time.sleep(60)
