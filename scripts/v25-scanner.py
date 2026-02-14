import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import sqlite3
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta

# ================= ⚙️ 策略配置 =================
SENDER_EMAIL = '371398370@qq.com'
SENDER_PASSWORD = 'hjqibancxrerbifb'
RECEIVER_EMAIL = '371398370@qq.com'

# 结构参数
MIN_HISTORY = 90
MAX_AMPLITUDE = 0.12
MIN_AMPLITUDE = 0.015
SQUEEZE_FACTOR = 0.75

# 过滤门槛
MIN_VOLUME_USDT = 3000000
VIP_MIN_VOLUME = 10000

# VIP 白名单
VIP_ASSETS = [
    'XAU', 'XAG', 'GOLD', 'SILVER',
    'EUR', 'GBP', 'JPY', 'AUD', 'CAD',
    'TSLA', 'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOG', 'COIN', 'MSTR',
    'SPX', 'NAS', 'US500', 'US100',
    'BTC', 'ETH', 'SOL', 'HYPE', 'PURR', 'KLAUS', 'TRUMP', 'MELANIA'
]

MIN_TOUCHES = 3
MIN_REJECTIONS = 1

DB_FILE = '/root/clawd/scripts/v25_data.db'
LOG_FILE = '/root/clawd/scripts/v25_run.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

# ================= 🌐 交易所 =================
EXCHANGES_TO_LOAD = {
    'okx':         {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'bitget':      {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'mexc':        {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'gate':        {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'hyperliquid': {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000}
}

exchanges_dict = {}
watchlist = {}
pending_confirms = {}
alert_history = {}

# 🔥🔥🔥 核心修改：双轨制信号量 🔥🔥🔥
# 给 CEX 强力并发，给 Hyperliquid 温柔对待
sem_general = asyncio.Semaphore(20)
sem_hyper = asyncio.Semaphore(2)     # Hyperliquid 专用限流阀 (最大并发2)

# ================= 🛡️ 智能 API 请求包装器 (防429核心) =================
async def safe_api_request(ex, func_name, *args, **kwargs):
    """
    统一接管所有 API 请求。
    1. 根据交易所自动选择信号量。
    2. 遇到 429 自动指数退避重试。
    """
    # 1. 选赛道
    current_sem = sem_hyper if ex.id == 'hyperliquid' else sem_general

    async with current_sem:
        retries = 3
        for i in range(retries):
            try:
                # 动态调用函数 (如 ex.fetch_ohlcv(*args))
                func = getattr(ex, func_name)
                return await func(*args, **kwargs)

            except Exception as e:
                # 2. 错误清洗
                err_msg = str(e).lower()
                is_limit = '429' in err_msg or 'too many requests' in err_msg or 'rate limit' in err_msg
                is_network = 'network' in err_msg or 'timeout' in err_msg

                if is_limit or is_network:
                    if i < retries - 1:
                        # 指数退避: 2s -> 4s -> 8s
                        sleep_time = (i + 1) * 2
                        if is_limit:
                            logging.warning(f"⚠️ {ex.id.upper()} 限流保护 (429)! 休息 {sleep_time}s 后重试...")
                        await asyncio.sleep(sleep_time)
                        continue

                # 如果是逻辑错误(如币种不存在)或重试耗尽，返回 None
                return None
        return None

# ================= 💾 数据库 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, base_vol REAL, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_confirms
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, direction TEXT, break_price REAL, candle_ts INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history
                 (uid TEXT PRIMARY KEY, last_alert TEXT)''')
    conn.commit()
    logging.info("✅ 数据库初始化成功")
    conn.close()

def db_crud(action, data=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if action == 'add_watch':
            c.execute("REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, base_vol, expiry) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['high'], data['low'], data['base_vol'], data['expiry'].isoformat()))
        elif action == 'remove_watch':
            c.execute("DELETE FROM watchlist WHERE uid=?", (data['uid'],))
        elif action == 'add_confirm':
            c.execute("REPLACE INTO pending_confirms (uid, exchange_id, symbol, direction, break_price, candle_ts) VALUES (?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['direction'], data['break_price'], data['candle_ts']))
        elif action == 'remove_confirm':
            c.execute("DELETE FROM pending_confirms WHERE uid=?", (data['uid'],))
        elif action == 'update_alert':
            c.execute("REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)", (data['uid'], data['time'].isoformat()))
        conn.commit()
    except Exception as e:
        logging.error(f"数据库操作失败 [{action}]: {e}")
    finally:
        conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        for row in c.execute("SELECT uid, last_alert FROM alert_history"):
            alert_history[row[0]] = datetime.fromisoformat(row[1])
        now = datetime.now()
        rows = c.execute("SELECT uid, exchange_id, symbol, high, low, base_vol, expiry FROM watchlist").fetchall()
        for row in rows:
            uid, ex_id, symbol, high, low, base_vol, expiry_str = row
            expiry = datetime.fromisoformat(expiry_str)
            if expiry <= now or ex_id not in exchanges_dict:
                db_crud('remove_watch', {'uid': uid})
                continue
            watchlist[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                'high': high, 'low': low, 'base_vol': base_vol, 'expiry': expiry
            }
        rows_conf = c.execute("SELECT uid, exchange_id, symbol, direction, break_price, candle_ts FROM pending_confirms").fetchall()
        for row in rows_conf:
            uid, ex_id, symbol, direction, break_price, candle_ts = row
            if ex_id not in exchanges_dict: continue
            pending_confirms[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                'direction': direction, 'break_price': break_price, 'candle_ts': candle_ts
            }
        logging.info(f"🔄 数据库恢复: {len(watchlist)} 盯盘, {len(pending_confirms)} 待确认.")
    except Exception as e:
        logging.error(f"数据库加载失败: {e}")
    finally:
        conn.close()

# ================= 📧 邮件 =================
def sync_send_email(subject, content, is_html=False):
    try:
        msg_type = 'html' if is_html else 'plain'
        msg = MIMEText(content, msg_type, 'utf-8')
        msg['From'] = formataddr(["V25抗压猎手", SENDER_EMAIL])
        msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
        msg['Subject'] = subject
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        logging.info(f"📧 邮件发送: {subject}")
        server.quit()
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

async def send_email(subject, content, is_html=False):
    await asyncio.to_thread(sync_send_email, subject, content, is_html)

# ================= 🚀 核心逻辑 =================

async def init_exchanges():
    logging.info("🔌 初始化交易所...")
    for ex_id, params in EXCHANGES_TO_LOAD.items():
        if hasattr(ccxt, ex_id):
            try:
                ex_class = getattr(ccxt, ex_id)
                exchanges_dict[ex_id] = ex_class(params)
                logging.info(f"✅ {ex_id.upper()} 就绪")
            except Exception as e:
                logging.error(f"❌ {ex_id} 初始化失败: {e}")
    if not exchanges_dict:
        logging.error("❌ 所有交易所初始化失败，退出")
        exit(1)

async def get_global_targets():
    logging.info("📡 拉取全市场实时行情...")
    global_targets = []

    async def fetch_markets(ex_id, ex):
        try:
            markets = await ex.load_markets()

            # 🔥 使用安全请求 wrapper
            tickers = await safe_api_request(ex, 'fetch_tickers')
            if not tickers: return

            is_dex = (ex_id == 'hyperliquid')

            for symbol, info in markets.items():
                if not info.get('active', True): continue
                if 'USDT' not in symbol and 'USDC' not in symbol and 'USD' not in symbol: continue

                if symbol not in tickers: continue
                vol = tickers[symbol].get('quoteVolume', 0)
                if vol is None: vol = 0

                if is_dex: threshold = 1000
                else:
                    is_vip = any(vip in symbol.split('/')[0] for vip in VIP_ASSETS)
                    threshold = VIP_MIN_VOLUME if is_vip else MIN_VOLUME_USDT

                if vol > threshold:
                    global_targets.append({'exchange': ex, 'symbol': symbol, 'vol': vol})
        except Exception as e:
            logging.error(f"{ex_id} fetch_markets异常: {e}")

    tasks = [fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()]
    await asyncio.gather(*tasks)
    return global_targets

async def check_structure(ex, symbol):
    # 这里不再需要 'with semaphore'，因为 safe_api_request 里已经有了
    try:
        # 🔥 使用安全请求 wrapper
        bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, timeframe='1h', limit=120)

        if not bars or len(bars) < MIN_HISTORY: return None

        df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        box = df.iloc[-(MIN_HISTORY+1) : -1]
        box_high, box_low = box['high'].max(), box['low'].min()

        amp = (box_high - box_low) / box_low
        if amp > MAX_AMPLITUDE or amp < MIN_AMPLITUDE: return None

        range_height = box_high - box_low
        upper_zone = box_high - (range_height * 0.15)
        lower_zone = box_low + (range_height * 0.15)

        touch_count = 0
        rejection_candles = 0

        for index, row in box.iterrows():
            is_touch = False
            is_rejection = False
            open_p, close_p, high_p, low_p = row['open'], row['close'], row['high'], row['low']
            body_size = abs(close_p - open_p)

            if high_p >= upper_zone:
                is_touch = True
                if (high_p - max(open_p, close_p)) > body_size * 1.5: is_rejection = True
            elif low_p <= lower_zone:
                is_touch = True
                if (min(open_p, close_p) - low_p) > body_size * 1.5: is_rejection = True

            if is_touch: touch_count += 1
            if is_rejection: rejection_candles += 1

        if touch_count < MIN_TOUCHES: return None
        if rejection_candles < MIN_REJECTIONS: return None

        avg_vol = (box['high'] - box['low']).mean()
        last_4 = box.iloc[-4:]
        recent_vol = (last_4['high'] - last_4['low']).mean()
        if recent_vol > avg_vol * SQUEEZE_FACTOR: return None

        return {
            'high': box_high, 'low': box_low, 'amp': amp,
            'squeeze': recent_vol/avg_vol, 'base_vol': avg_vol,
            'touches': touch_count, 'rejections': rejection_candles
        }
    except Exception as e:
        logging.error(f"{symbol} check_structure异常: {e}")
        return None

async def radar_job():
    """雷达：静默入库"""
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logging.info(f"🔍 扫描 {len(targets)} 个标的...")

                async def check_wrapper(ex, symbol, uid):
                    if uid in watchlist: return None
                    struct = await check_structure(ex, symbol)
                    if struct: return (ex, symbol, uid, struct)
                    return None

                tasks = [asyncio.create_task(check_wrapper(t['exchange'], t['symbol'], f"{t['exchange'].id}:{t['symbol']}")) for t in targets]
                results = await asyncio.gather(*tasks)

                count_new = 0
                for res in results:
                    if res:
                        ex, symbol, uid, struct = res
                        expiry = datetime.now() + timedelta(hours=4)
                        data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol,
                                'high': struct['high'], 'low': struct['low'],
                                'base_vol': struct['base_vol'], 'expiry': expiry}
                        watchlist[uid] = {'exchange': ex, 'symbol': symbol,
                                          'high': struct['high'], 'low': struct['low'],
                                          'base_vol': struct['base_vol'], 'expiry': expiry}
                        db_crud('add_watch', data)
                        count_new += 1
                if count_new > 0:
                    logging.info(f"🤫 静默锁定 {count_new} 个新目标")

        except Exception as e: logging.error(f"雷达异常: {e}")
        await asyncio.sleep(3600)

async def sniper_job():
    """狙击手"""
    while True:
        start = time.time()
        if watchlist:
            tasks = []
            for uid in list(watchlist.keys()):
                info = watchlist[uid]
                if datetime.now() > info['expiry']:
                    del watchlist[uid]
                    db_crud('remove_watch', {'uid': uid})
                    continue
                tasks.append(asyncio.create_task(snip_target(uid, info)))
            await asyncio.gather(*tasks)
        await asyncio.sleep(max(60 - (time.time() - start), 1))

async def snip_target(uid, info):
    try:
        ex, symbol = info['exchange'], info['symbol']

        # 🔥 使用安全请求 wrapper
        ticker = await safe_api_request(ex, 'fetch_ticker', symbol)
        if not ticker: return

        price = ticker['last']
        signal, break_price, direction = None, None, None
        if price > info['high']:
            signal, break_price, direction = "📈 向上突破", info['high'], 'up'
        elif price < info['low']:
            signal, break_price, direction = "📉 向下跌破", info['low'], 'down'

        if signal:
            logging.info(f"⚡ {symbol} 突破，二审中...")

            # 🔥 使用安全请求 wrapper
            recent_bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', limit=12)
            if not recent_bars: return

            base_check_bars = recent_bars[-10:-3]
            if len(base_check_bars) < 5: return

            check_vol_sum = sum([bar[2]-bar[3] for bar in base_check_bars])
            check_vol_avg = check_vol_sum / len(base_check_bars)
            base_vol = info.get('base_vol', 999999)

            if check_vol_avg > base_vol * 1.2:
                logging.warning(f"❌ {symbol} 二审失败")
                del watchlist[uid]
                db_crud('remove_watch', {'uid': uid})
                return

            logging.info(f"✅ {symbol} 二审通过！")

            # 1. 立即发送第一封邮件 (急件)
            content = f"""
            <h2>🚀 瞬时突破警报 (V25)</h2>
            <p><b>方向:</b> <span style="color: {'red' if '跌' in signal else 'green'}; font-size: 18px;">{signal}</span></p>
            <p><b>平台:</b> {ex.id.upper()}</p>
            <p><b>品种:</b> {symbol}</p>
            <p><b>现价:</b> {price}</p>
            <p><b>突破位:</b> {break_price}</p>
            <p>⚠️ <b>注意：</b>等待整点收线确认。</p>
            """
            asyncio.create_task(send_email(f"🚀 {signal} {symbol}", content, is_html=True))

            # 2. 移出 Watchlist，加入 Pending Confirm (收线确认区)
            # 计算当前K线的时间戳 (整点)
            current_ts = int(time.time() * 1000)
            candle_ts = current_ts - (current_ts % 3600000)

            pending_data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol,
                            'direction': direction, 'break_price': break_price, 'candle_ts': candle_ts}
            pending_confirms[uid] = {'exchange': ex, 'symbol': symbol, 'direction': direction,
                                     'break_price': break_price, 'candle_ts': candle_ts}
            db_crud('add_confirm', pending_data)

            del watchlist[uid]
            db_crud('remove_watch', {'uid': uid})
    except Exception as e:
        logging.error(f"狙击任务异常 [{info['symbol']}]: {e}")

async def confirmation_job():
    """确权官：每分钟检查已收线的K线，确认实体突破"""
    while True:
        try:
            if pending_confirms:
                confirmed_list = []
                current_ts = int(time.time() * 1000)

                # 遍历待确认列表
                for uid in list(pending_confirms.keys()):
                    item = pending_confirms[uid]
                    # 检查是否已经收线 (当前时间 > K线开始时间 + 1小时 + 1分钟缓冲)
                    if current_ts > (item['candle_ts'] + 3600000 + 60000):
                        ex = item['exchange']
                        symbol = item['symbol']

                        # 拉取那根特定的K线
                        # fetch_ohlcv 这里的 since 参数非常关键
                        candle_data = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', since=item['candle_ts'], limit=1)

                        if candle_data and len(candle_data) > 0:
                            candle = candle_data[0]
                            # candle结构: [ts, open, high, low, close, vol]
                            close_price = candle[4]
                            break_price = item['break_price']
                            direction = item['direction']

                            is_valid = False
                            if direction == 'up' and close_price > break_price:
                                is_valid = True
                            elif direction == 'down' and close_price < break_price:
                                is_valid = True

                            if is_valid:
                                confirmed_list.append({
                                    'exchange': ex.id.upper(), 'symbol': symbol,
                                    'direction': '做多' if direction == 'up' else '做空',
                                    'close': close_price, 'break': break_price
                                })
                                logging.info(f"✅ {symbol} 收线确认有效！(收盘:{close_price} > 突破:{break_price})")
                            else:
                                logging.warning(f"❌ {symbol} 假突破 (收盘:{close_price} 未站稳)，已丢弃。")

                        # 无论成功失败，都移除任务
                        del pending_confirms[uid]
                        db_crud('remove_confirm', {'uid': uid})

                # 如果有确认有效的，打包发送
                if confirmed_list:
                    html = """
                    <h3>✅ 突破有效性确认日报</h3>
                    <p>以下品种已完成整点收线，且实体站稳突破位，非假突破：</p>
                    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse;">
                        <tr style="background-color: #e6fffa;"><th>平台</th><th>品种</th><th>方向</th><th>突破位</th><th>收盘价(实体)</th></tr>
                    """
                    for c in confirmed_list:
                        color = 'green' if c['direction']=='做多' else 'red'
                        html += f"<tr><td>{c['exchange']}</td><td><b>{c['symbol']}</b></td><td style='color:{color}'>{c['direction']}</td><td>{c['break']}</td><td>{c['close']}</td></tr>"
                    html += "</table><p>建议：可根据回踩情况择机入场。</p>"

                    await send_email(f"✅ {len(confirmed_list)} 个突破已确认有效", html, is_html=True)

        except Exception as e: logging.error(f"确认任务异常: {e}")
        await asyncio.sleep(60)

async def main():
    print("🚀 V25.0 抗压版启动 (Hyperliquid 防429优化)")
    init_db()
    await init_exchanges()
    load_data_from_db()
    await asyncio.gather(radar_job(), sniper_job(), confirmation_job())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 V25 正常退出")
    except Exception as e:
        logging.error(f"❌ 程序异常退出: {e}")
