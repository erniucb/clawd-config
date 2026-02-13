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
MIN_VOLUME_USDT = 3000000  # CEX 门槛
VIP_MIN_VOLUME = 10000     # VIP 门槛

# VIP 白名单
VIP_ASSETS = [
    'XAU', 'XAG', 'GOLD', 'SILVER',       # 贵金属
    'EUR', 'GBP', 'JPY', 'AUD', 'CAD',    # 外汇
    'TSLA', 'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOG', 'COIN', 'MSTR', # 美股
    'SPX', 'NAS', 'US500', 'US100',        # 指数
    'BTC', 'ETH', 'SOL', 'HYPE', 'PURR', 'KLAUS', 'TRUMP', 'MELANIA' # 热门加密货币
]

MIN_TOUCHES = 3
MIN_REJECTIONS = 1

# 数据库与日志（绝对路径）
DB_FILE = '/root/clawd/scripts/v20_data.db'
LOG_FILE = '/root/clawd/scripts/v20_run.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

# ================= 🌐 交易所联盟 =================
EXCHANGES_TO_LOAD = {
    'okx':         {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'bitget':      {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'mexc':        {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'gate':        {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'hyperliquid': {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000}
}

exchanges_dict = {}
watchlist = {}
alert_history = {}
semaphore = asyncio.Semaphore(15)

# ================= 💾 数据库 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history
                 (uid TEXT PRIMARY KEY, last_alert TEXT)''')
    conn.commit()
    conn.close()

def db_crud(action, data=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        if action == 'add':
            c.execute("REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, expiry) VALUES (?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['high'], data['low'], data['expiry'].isoformat()))
        elif action == 'remove':
            c.execute("DELETE FROM watchlist WHERE uid=?", (data['uid'],))
        elif action == 'update_alert':
            c.execute("REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)", (data['uid'], data['time'].isoformat()))
        conn.commit()
    except Exception as e:
        logging.error(f"DB Error: {e}")
    finally:
        conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        for row in c.execute("SELECT uid, last_alert FROM alert_history"):
            alert_history[row[0]] = datetime.fromisoformat(row[1])

        count = 0
        now = datetime.now()
        rows = c.execute("SELECT uid, exchange_id, symbol, high, low, expiry FROM watchlist").fetchall()
        for row in rows:
            uid, ex_id, symbol, high, low, expiry_str = row
            expiry = datetime.fromisoformat(expiry_str)
            if expiry <= now or ex_id not in exchanges_dict:
                db_crud('remove', {'uid': uid})
                continue
            watchlist[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                'high': high, 'low': low, 'expiry': expiry
            }
            count += 1
        logging.info(f"🔄 数据库恢复: {count} 个任务.")
    except Exception as e:
        logging.error(f"Load DB Error: {e}")
    finally:
        conn.close()

# ================= 📧 邮件 =================
def sync_send_email(subject, content, is_html=False):
    try:
        msg_type = 'html' if is_html else 'plain'
        msg = MIMEText(content, msg_type, 'utf-8')
        msg['From'] = formataddr(["V20猎手", SENDER_EMAIL])
        msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
        msg['Subject'] = subject
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        logging.info(f"📧 邮件发送: {subject}")
    except Exception as e:
        logging.error(f"❌ 邮件失败: {e}")

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
                logging.warning(f"⚠️ {ex_id.upper()} 加载失败: {e}")
        else:
            logging.warning(f"❌ 请更新 ccxt: pip install -U ccxt")
    if not exchanges_dict:
        logging.error("❌ 无可用交易所，请检查网络！")
        exit()

async def get_global_targets():
    logging.info("📡 拉取全市场实时行情...")
    global_targets = []

    for ex_id, ex in exchanges_dict.items():
        try:
            logging.info(f"  📡 {ex_id.upper()}: 加载市场...")
            markets = await ex.load_markets()

            try:
                tickers = await ex.fetch_tickers()
            except Exception as e:
                logging.warning(f"  - {ex_id.upper()} fetch_tickers 失败: {e}")
                continue

            count_pass = 0
            is_dex = (ex_id == 'hyperliquid')

            for symbol, info in markets.items():
                if not info.get('active', True): continue
                if 'USDT' not in symbol and 'USDC' not in symbol and 'USD' not in symbol:
                    continue

                if symbol not in tickers: continue
                ticker_data = tickers[symbol]

                vol = ticker_data.get('quoteVolume', 0)
                if vol is None: vol = 0

                if is_dex:
                    threshold = 1000
                else:
                    is_vip = any(vip in symbol.split('/')[0].split(':')[0] for vip in VIP_ASSETS)
                    threshold = VIP_MIN_VOLUME if is_vip else MIN_VOLUME_USDT

                if vol > threshold:
                    global_targets.append({'exchange': ex, 'symbol': symbol, 'vol': vol})
                    count_pass += 1

            logging.info(f"  - {ex_id.upper()}: 筛选出 {count_pass} 个活跃标的")
        except Exception as e:
            logging.warning(f"  - ⚠️ {ex_id.upper()} 处理异常: {e}")

    return global_targets

async def check_structure(ex, symbol):
    async with semaphore:
        try:
            bars = await ex.fetch_ohlcv(symbol, timeframe='1h', limit=120)
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

            last_4 = box.iloc[-4:]
            avg_vol = (box['high'] - box['low']).mean()
            recent_vol = (last_4['high'] - last_4['low']).mean()
            if recent_vol > avg_vol * SQUEEZE_FACTOR: return None

            return {
                'high': box_high, 'low': box_low, 'amp': amp,
                'squeeze': recent_vol/avg_vol,
                'touches': touch_count, 'rejections': rejection_candles
            }
        except:
            return None

async def radar_job():
    """雷达模式：扫描 -> 去重 -> 发送"""
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logging.info(f"🔍 扫描 {len(targets)} 个标的...")

                new_findings = []

                tasks = []
                async def check_wrapper(ex, symbol, uid):
                    if uid in watchlist: return None
                    struct = await check_structure(ex, symbol)
                    if struct:
                        return (ex, symbol, uid, struct)
                    return None

                for target in targets:
                    ex = target['exchange']
                    symbol = target['symbol']
                    uid = f"{ex.id}:{symbol}"
                    tasks.append(asyncio.create_task(check_wrapper(ex, symbol, uid)))

                results = await asyncio.gather(*tasks)

                for res in results:
                    if res:
                        ex, symbol, uid, struct = res
                        expiry = datetime.now() + timedelta(hours=4)

                        # 存入数据库 (保持各交易所独立，确保 Sniper 监控准确)
                        data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol, 'high': struct['high'], 'low': struct['low'], 'expiry': expiry}
                        watchlist[uid] = {'exchange': ex, 'symbol': symbol, 'high': struct['high'], 'low': struct['low'], 'expiry': expiry}
                        db_crud('add', data)

                        # 加入待处理列表 (包含用于排序的原始分数)
                        new_findings.append({
                            'exchange': ex.id.upper(),
                            'symbol': symbol,
                            'price_range': f"{struct['low']} - {struct['high']}",
                            'amp': f"{round(struct['amp']*100, 2)}%",
                            'score_text': f"触:{struct['touches']} / 拒:{struct['rejections']}",
                            'raw_score': struct['touches'] + struct['rejections'] * 2 # 加权分：拒绝形态更值钱
                        })
                        logging.info(f"🎯 锁定: {ex.id.upper()} {symbol}")

                # 智能去重逻辑
                if new_findings:
                    logging.info(f"📦 发现 {len(new_findings)} 个原始信号，正在智能去重...")

                    # 1. 按 symbol 归类
                    merged_map = {}
                    for item in new_findings:
                        sym = item['symbol']
                        if sym not in merged_map:
                            merged_map[sym] = {
                                'platforms': [item['exchange']],
                                'display_data': item # 默认展示第一个
                            }
                        else:
                            merged_map[sym]['platforms'].append(item['exchange'])
                            # 2. 优选：如果当前这个交易所的形态评分更高，就用它的数据展示
                            if item['raw_score'] > merged_map[sym]['display_data']['raw_score']:
                                merged_map[sym]['display_data'] = item

                    # 3. 生成去重后的 HTML
                    html_content = f"""
                    <h3>🚀 猎手雷达日报 (已聚合 {len(merged_map)} 个独立品种)</h3>
                    <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                        <tr style="background-color: #f2f2f2;">
                            <th>品种</th>
                            <th>涉及平台</th>
                            <th>最佳结构 (支撑-阻力)</th>
                            <th>振幅</th>
                            <th>形态评分</th>
                        </tr>
                    """

                    for sym, data in merged_map.items():
                        best = data['display_data']
                        platforms_str = ", ".join(sorted(list(set(data['platforms'])))) # 去重排序

                        html_content += f"""
                        <tr>
                            <td><b>{sym}</b></td>
                            <td>{platforms_str}</td>
                            <td>{best['price_range']}</td>
                            <td>{best['amp']}</td>
                            <td>{best['score_text']}</td>
                        </tr>
                        """

                    html_content += "</table><p>注：展示数据取自形态评分最高的交易所。所有涉及平台均已加入毫秒级独立盯盘。</p>"

                    await send_email(f"【雷达日报】发现 {len(merged_map)} 个收敛结构", html_content, is_html=True)
                else:
                    logging.info("💤 本轮无新发现.")

        except Exception as e:
            logging.error(f"雷达异常: {e}")
        await asyncio.sleep(3600)

async def sniper_job():
    """狙击手：保持单条极速发送"""
    while True:
        start = time.time()
        if watchlist:
            tasks = []
            for uid in list(watchlist.keys()):
                info = watchlist[uid]
                if datetime.now() > info['expiry']:
                    del watchlist[uid]
                    db_crud('remove', {'uid': uid})
                    continue
                tasks.append(asyncio.create_task(snip_target(uid, info)))
            await asyncio.gather(*tasks)
        await asyncio.sleep(max(60 - (time.time() - start), 1))

async def snip_target(uid, info):
    try:
        ex, symbol = info['exchange'], info['symbol']
        ticker = await ex.fetch_ticker(symbol)
        price = ticker['last']

        signal, break_price = None, None
        if price > info['high']: signal, break_price = "📈 向上突破", info['high']
        elif price < info['low']: signal, break_price = "📉 向下跌破", info['low']

        if signal:
            logging.warning(f"🚀 {symbol} 突破! 现价:{price}")
            if uid not in alert_history or datetime.now() - alert_history[uid] > timedelta(hours=1):
                content = f"""
                <h2>🚨 结构突破警报</h2>
                <p><b>方向:</b> <span style="color: {'red' if '跌' in signal else 'green'}; font-size: 18px;">{signal}</span></p>
                <p><b>平台:</b> {ex.id.upper()}</p>
                <p><b>品种:</b> {symbol}</p>
                <p><b>现价:</b> {price}</p>
                <p><b>突破关键位:</b> {break_price}</p>
                <p>主力已动手，请立即查看图表！</p>
                """
                asyncio.create_task(send_email(f"🚨 {signal} {symbol}", content, is_html=True))

                alert_history[uid] = datetime.now()
                db_crud('update_alert', {'uid': uid, 'time': datetime.now()})
                del watchlist[uid]
                db_crud('remove', {'uid': uid})
    except:
        pass

async def main():
    print("🚀 V20.0 智能去重版启动")
    init_db()
    await init_exchanges()
    load_data_from_db()
    await asyncio.gather(radar_job(), sniper_job())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
