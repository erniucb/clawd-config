import asyncio
import ccxt.async_support as ccxt  # 🔥 核心升级：引入 CCXT 的异步引擎
import pandas as pd
import sqlite3
import logging
import smtplib
import time
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta

# ================= ⚙️ 工业级配置 =================
SENDER_EMAIL = '371398370@qq.com'
SENDER_PASSWORD = 'hjqibancxrerbifb'
RECEIVER_EMAIL = '371398370@qq.com'

MIN_HISTORY = 90
MAX_AMPLITUDE = 0.10
SQUEEZE_FACTOR = 0.75
MIN_VOLUME_USDT = 5000000

DB_FILE = '/root/clawd/scripts/hunter_data.db'
LOG_FILE = '/root/clawd/scripts/hunter_run.log'

# ================= 📝 专业日志系统 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================= 🌐 异步交易所池 =================
EXCHANGES_TO_LOAD = {
    'binance': {'enableRateLimit': True, 'options': {'defaultType': 'future'}, 'timeout': 30000},
    'bybit':   {'enableRateLimit': True, 'options': {'defaultType': 'linear'}, 'timeout': 30000},
    'bitget':  {'enableRateLimit': True, 'options': {'defaultType': 'swap'},   'timeout': 30000},
    'bingx':   {'enableRateLimit': True, 'options': {'defaultType': 'swap'},   'timeout': 30000},
    'msx':     {'enableRateLimit': True, 'options': {'defaultType': 'swap'},   'timeout': 30000}
}

exchanges_dict = {}
watchlist = {}
alert_history = {}

# API 并发控制器 (最大同时发送 10 个请求，防止被交易所封 IP)
semaphore = asyncio.Semaphore(10)

# ================= 💾 SQLite 数据库 (保持同步即可，操作极快) =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history
                 (uid TEXT PRIMARY KEY, last_alert TEXT)''')
    conn.commit()
    conn.close()

def db_add_watchlist(uid, ex_id, symbol, high, low, expiry):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, expiry) VALUES (?, ?, ?, ?, ?, ?)",
              (uid, ex_id, symbol, high, low, expiry.isoformat()))
    conn.commit()
    conn.close()

def db_remove_watchlist(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE uid=?", (uid,))
    conn.commit()
    conn.close()

def db_update_alert(uid, alert_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)", (uid, alert_time.isoformat()))
    conn.commit()
    conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for row in c.execute("SELECT uid, last_alert FROM alert_history"):
        alert_history[row[0]] = datetime.fromisoformat(row[1])

    restored_count = 0
    now = datetime.now()
    for row in c.execute("SELECT uid, exchange_id, symbol, high, low, expiry FROM watchlist").fetchall():
        uid, ex_id, symbol, high, low, expiry_str = row
        expiry = datetime.fromisoformat(expiry_str)
        if expiry <= now or ex_id not in exchanges_dict:
            db_remove_watchlist(uid)
            continue
        watchlist[uid] = {
            'exchange': exchanges_dict[ex_id], 'symbol': symbol,
            'high': high, 'low': low, 'expiry': expiry
        }
        restored_count += 1
    conn.close()
    logging.info(f"🔄 数据库恢复完成: {restored_count} 个盯盘任务.")

# ================= 📧 邮件系统 (放入后台线程，不阻塞主循环) =================
def sync_send_email(subject, content):
    """同步发送邮件的底层函数"""
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr(["万物并集猎手", SENDER_EMAIL])
        msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
        msg['Subject'] = subject

        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        logging.info(f"📧 邮件已发送: {subject}")
    except Exception as e:
        logging.error(f"❌ 邮件发送失败: {e}")

async def send_email(subject, content):
    """异步包装器：让邮件发送在独立线程执行，绝对不卡顿盯盘"""
    await asyncio.to_thread(sync_send_email, subject, content)

# ================= 🚀 核心异步逻辑 =================

async def init_exchanges():
    logging.info("🔌 正在初始化异步交易所联盟...")
    for ex_id, params in EXCHANGES_TO_LOAD.items():
        if hasattr(ccxt, ex_id):
            try:
                ex_class = getattr(ccxt, ex_id)
                exchanges_dict[ex_id] = ex_class(params)
                logging.info(f"✅ 异步加载成功: {ex_id.upper()}")
            except Exception as e:
                logging.warning(f"⚠️ {ex_id.upper()} 初始化失败: {e}")
    if not exchanges_dict:
        logging.error("❌ 无可用交易所，退出！")
        exit()

async def get_global_targets():
    logging.info("📡 开始拉取全市场数据...")
    global_targets = []

    # 并发获取所有交易所的市场数据
    async def fetch_markets(ex_id, ex):
        try:
            markets = await ex.load_markets()
            count = 0
            for symbol, info in markets.items():
                if not (symbol.endswith(':USDT') or symbol.endswith('/USDT')): continue
                if not info.get('active', True): continue
                vol = info.get('quoteVolume', 0)
                if vol and vol > MIN_VOLUME_USDT:
                    global_targets.append({'exchange': ex, 'symbol': symbol, 'vol': vol})
                    count += 1
            logging.info(f"  - {ex_id.upper()}: {count} 个活跃标的")
        except Exception as e:
            logging.warning(f"  - ⚠️ 无法拉取 {ex_id.upper()}: {e}")

    # 同时发车！
    tasks = [fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()]
    await asyncio.gather(*tasks)

    global_targets = sorted(global_targets, key=lambda x: x['vol'], reverse=True)
    return global_targets

async def check_structure(ex, symbol):
    """并发形态检测"""
    async with semaphore:  # 保护机制：最多同时发出10个请求
        try:
            bars = await ex.fetch_ohlcv(symbol, timeframe='1h', limit=120)
            if not bars or len(bars) < MIN_HISTORY: return None

            df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            box = df.iloc[-(MIN_HISTORY+1) : -1]

            box_high, box_low = box['high'].max(), box['low'].min()
            amp = (box_high - box_low) / box_low
            if amp > MAX_AMPLITUDE or amp < 0.01: return None

            last_4 = box.iloc[-4:]
            avg_vol = (box['high'] - box['low']).mean()
            recent_vol = (last_4['high'] - last_4['low']).mean()

            if recent_vol > avg_vol * SQUEEZE_FACTOR: return None

            return {'high': box_high, 'low': box_low, 'amp': amp, 'squeeze': recent_vol/avg_vol}
        except Exception:
            return None

async def radar_job():
    """雷达扫描任务：每小时执行一次"""
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logging.info(f"🔍 开始并发分析 {len(targets)} 个标的 K 线形态...")

                # 创建所有 K线 分析任务
                tasks = []
                for target in targets:
                    ex = target['exchange']
                    symbol = target['symbol']
                    uid = f"{ex.id}:{symbol}"
                    if uid not in watchlist:
                        tasks.append(asyncio.create_task(process_single_target(ex, symbol, uid)))

                # 等待所有分析完成 (以前要10分钟，现在只要几十秒！)
                await asyncio.gather(*tasks)
                logging.info("✅ 本轮全域雷达并发扫描完成。")

        except Exception as e:
            logging.error(f"雷达任务异常: {e}")

        # 睡一小时，再去扫
        await asyncio.sleep(3600)

async def process_single_target(ex, symbol, uid):
    """处理单个标的的回调函数"""
    struct = await check_structure(ex, symbol)
    if struct:
        expiry_time = datetime.now() + timedelta(hours=4)
        watchlist[uid] = {
            'exchange': ex, 'symbol': symbol, 'expiry': expiry_time,
            'high': struct['high'], 'low': struct['low']
        }
        db_add_watchlist(uid, ex.id, symbol, struct['high'], struct['low'], expiry_time)

        logging.info(f"🎯 锁定目标: [{ex.id.upper()}] {symbol}")
        # 异步发邮件，不卡流程
        asyncio.create_task(send_email(
            f"【并集发现】{symbol} 在 {ex.id.upper()} 收敛",
            f"平台: {ex.id.upper()}\n品种: {symbol}\n阻力: {struct['high']}\n支撑: {struct['low']}"
        ))

async def sniper_job():
    """狙击手任务：死死盯住 Watchlist，严格每 60 秒开火一次"""
    while True:
        start_time = time.time()

        if watchlist:
            # logging.info(f"🔫 狙击手巡视中... 当前目标数: {len(watchlist)}")
            tasks = []
            for uid in list(watchlist.keys()):
                info = watchlist[uid]
                ex = info['exchange']
                symbol = info['symbol']

                if datetime.now() > info['expiry']:
                    del watchlist[uid]
                    db_remove_watchlist(uid)
                    logging.info(f"🗑️ 目标过期: {uid}")
                    continue

                # 派发并发盯盘任务
                tasks.append(asyncio.create_task(snip_single_target(uid, ex, symbol, info)))

            await asyncio.gather(*tasks)

        # 精确的 60 秒节拍器补偿
        elapsed = time.time() - start_time
        sleep_time = max(60 - elapsed, 1) # 至少睡 1 秒防死循环
        await asyncio.sleep(sleep_time)

async def snip_single_target(uid, ex, symbol, info):
    """并发查询最新价，判断突破"""
    try:
        # 获取最新价 (走网络请求，但被 async 挂起，不会阻塞别人)
        ticker = await ex.fetch_ticker(symbol)
        price = ticker['last']

        signal, break_price = None, None
        if price > info['high']: signal, break_price = "📈 向上突破", info['high']
        elif price < info['low']: signal, break_price = "📉 向下跌破", info['low']

        if signal:
            logging.warning(f"🚀 【击杀确认】 {ex.id.upper()} 的 {symbol} 触发突破！现价: {price}")

            if uid not in alert_history or datetime.now() - alert_history[uid] > timedelta(hours=1):
                email_content = f"🚨 【并集突破警报】{symbol}\n\n平台: {ex.id.upper()}\n方向: {signal}\n现价: {price}\n突破位: {break_price}\n\n快去查看！"

                # 异步发邮件
                asyncio.create_task(send_email(f"🚨 {signal} {symbol} ({ex.id.upper()})", email_content))

                alert_history[uid] = datetime.now()
                db_update_alert(uid, datetime.now())

                del watchlist[uid]
                db_remove_watchlist(uid)
    except Exception as e:
        pass # 网络抖动，忽略，等下一个 60 秒

async def main():
    print("===================================================")
    print("🚀 万物并集猎手 V11.0 (Asyncio 并发超跑版) 启动...")
    print("===================================================")

    init_db()
    await init_exchanges()
    load_data_from_db()

    # 🔥 见证奇迹的时刻：雷达和狙击手作为两个独立的并发协程同时运行！
    # 互不干扰，雷达扫得再慢，狙击手也会准时在第 60 秒开枪。
    await asyncio.gather(
        radar_job(),
        sniper_job()
    )

if __name__ == "__main__":
    try:
        # 启动 Python 异步事件循环
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 接收到退出指令，程序安全终止。")
