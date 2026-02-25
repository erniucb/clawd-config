import asyncio
import aiohttp
import ccxt.async_support as ccxt
import pandas as pd
import sqlite3
import logging
import time
import json
from datetime import datetime, timedelta, timezone

# ================= ⚙️ 策略与系统配置 =================
# 飞书机器人配置
FEISHU_APP_ID = 'cli_a9177b28e6f89cd4'
FEISHU_APP_SECRET = 'zJniiJUj8SHJbRO9DuiEYIBfHJv6gkfA'
FEISHU_USER_OPENID = 'ou_0058e09903092b62b45494eace8ab02f'

# 威科夫箱体 ATR 自适应参数
MIN_HISTORY = 90           # 历史K线数量
ATR_MULTIPLIER_MIN = 1.5   # 箱体振幅必须 >= 1.5倍 90小时ATR
ATR_MULTIPLIER_MAX = 4.0   # 箱体振幅必须 <= 4.0倍 90小时ATR
EDGE_ZONE_RATIO = 0.03     # 边缘区比例 3% (测试与拒绝的极限区)
SQUEEZE_FACTOR = 0.75      # 收敛系数：末端4根ATR <= 全局ATR * 0.75
BASE_CHECK_FACTOR = 1.2    # 基座安检：突破前7根K线ATR <= 全局ATR * 1.2

# 过滤门槛
MIN_VOLUME_USDT = 3000000  # 普通CEX资产门槛 300万 U
VIP_MIN_VOLUME = 10000     # VIP资产门槛 1万 U
DEX_MIN_VOLUME = 1000      # Hyperliquid DEX门槛 1000 U

VIP_ASSETS = [
    'XAU', 'XAG', 'GOLD', 'SILVER', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD',    
    'TSLA', 'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOG', 'COIN', 'MSTR', 
    'SPX', 'NAS', 'US500', 'US100', 'BTC', 'ETH', 'SOL', 'HYPE', 'PURR'
]

MIN_TOUCHES = 3            
MIN_REJECTIONS = 1         

DB_FILE = '/root/clawd/scripts/v28_wyckoff_atr.db' 
LOG_FILE = '/root/clawd/scripts/v28_engine.log'

tz_utc_8 = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

# ================= 🌐 交易所并发与防限流 =================
EXCHANGES_TO_LOAD = {
    'okx':         {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'bitget':      {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'mexc':        {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000},
    'hyperliquid': {'enableRateLimit': True, 'options': {'defaultType': 'swap'}, 'timeout': 30000}
}

exchanges_dict = {}  
watchlist = {}          
pending_confirms = {}   

sem_general = asyncio.Semaphore(20)  
sem_hyper = asyncio.Semaphore(2)     

# 🔥 核心解耦：全局异步消息队列
notify_queue = asyncio.Queue()

# ================= 🎯 飞书Token管理 =================
feishu_access_token = None
feishu_token_expiry = 0

async def get_feishu_token():
    """获取飞书 tenant_access_token，自动刷新"""
    global feishu_access_token, feishu_token_expiry
    
    # 如果token还有效，直接返回
    if feishu_access_token and time.time() < feishu_token_expiry:
        return feishu_access_token
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": FEISHU_APP_ID,
                    "app_secret": FEISHU_APP_SECRET
                },
                timeout=10.0
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('code') == 0:
                        feishu_access_token = data['tenant_access_token']
                        feishu_token_expiry = time.time() + data['expire'] - 300  # 提前5分钟刷新
                        logging.info("🔄 飞书Token已刷新")
                        return feishu_access_token
                    else:
                        logging.error(f"获取飞书Token失败: {data}")
                        return None
                else:
                    logging.error(f"获取飞书Token HTTP错误: {resp.status}")
                    return None
    except Exception as e:
        logging.error(f"获取飞书Token异常: {e}")
        return None

async def safe_api_request(ex, func_name, *args, **kwargs):
    current_sem = sem_hyper if ex.id == 'hyperliquid' else sem_general
    async with current_sem:
        retries = 3
        for i in range(retries):
            try:
                func = getattr(ex, func_name)
                return await asyncio.wait_for(func(*args, **kwargs), timeout=10.0) # 10秒强制熔断防卡死
            except Exception as e:
                err_msg = str(e).lower()
                is_limit = '429' in err_msg or 'too many requests' in err_msg or 'rate limit' in err_msg
                is_network = 'network' in err_msg or 'timeout' in err_msg
                if is_limit or is_network:
                    if i < retries - 1:
                        sleep_time = (2 ** i) * 2 
                        await asyncio.sleep(sleep_time)
                        continue
                return None
        return None

# ================= 💾 数据库防灾固化 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, atr_90 REAL, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_confirms
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, direction TEXT, break_price REAL, close_ts INTEGER, breakout_time TEXT)''')
    conn.commit()
    conn.close()

def db_crud(action, data=None):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    c = conn.cursor()
    try:
        if action == 'add_watch':
            c.execute("REPLACE INTO watchlist VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['high'], data['low'], data['atr_90'], data['expiry'].isoformat()))
        elif action == 'remove_watch':
            c.execute("DELETE FROM watchlist WHERE uid=?", (data['uid'],))
        elif action == 'add_confirm':
            c.execute("REPLACE INTO pending_confirms VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['direction'], data['break_price'], data['close_ts'], data['breakout_time']))
        elif action == 'remove_confirm':
            c.execute("DELETE FROM pending_confirms WHERE uid=?", (data['uid'],))
        conn.commit()
    except Exception as e: logging.error(f"数据库操作失败: {e}")
    finally: conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        now_utc8 = datetime.now(tz_utc_8)
        rows = c.execute("SELECT * FROM watchlist").fetchall()
        for row in rows:
            uid, ex_id, symbol, high, low, atr_90, expiry_str = row
            expiry = datetime.fromisoformat(expiry_str)
            if expiry.replace(tzinfo=tz_utc_8) <= now_utc8 or ex_id not in exchanges_dict:
                db_crud('remove_watch', {'uid': uid})
                continue
            watchlist[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                'high': high, 'low': low, 'atr_90': atr_90, 'expiry': expiry
            }
            
        rows_conf = c.execute("SELECT * FROM pending_confirms").fetchall()
        for row in rows_conf:
            uid, ex_id, symbol, direction, break_price, close_ts, breakout_time = row
            if ex_id not in exchanges_dict: continue
            pending_confirms[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                'direction': direction, 'break_price': break_price, 
                'close_ts': close_ts, 'breakout_time': breakout_time
            }
    except Exception: pass
    finally: conn.close()

# ================= 📧 飞书异步发信员 =================
async def feishu_worker():
    """专职发信死循环，彻底解耦，绝不阻塞主交易流程"""
    async with aiohttp.ClientSession() as session:
        while True:
            payload = await notify_queue.get()
            try:
                token = await get_feishu_token()
                if not token:
                    logging.error("无法获取飞书Token，跳过发送")
                    notify_queue.task_done()
                    continue
                
                # 使用飞书 REST API 发送消息
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=5.0
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logging.error(f"飞书推送失败, 状态码: {resp.status}, 错误: {error_text}")
                    else:
                        resp_data = await resp.json()
                        if resp_data.get('code') == 0:
                            logging.info(f"✅ 飞书消息发送成功: {payload.get('msg_type')}")
                        else:
                            logging.error(f"飞书API错误: {resp_data}")
            except Exception as e:
                logging.error(f"发信员网络异常: {e}")
            finally:
                notify_queue.task_done()

def build_feishu_card(title, content_md, color="blue"):
    """构建精美的飞书 Interactive 卡片"""
    return {
        "receive_id": FEISHU_USER_OPENID,
        "msg_type": "interactive",
        "receive_id_type": "open_id",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": color
            },
            "elements": [{"tag": "markdown", "content": content_md}]
        }
    }

# ================= 🚀 核心交易逻辑 =================
async def init_exchanges():
    for ex_id, params in EXCHANGES_TO_LOAD.items():
        if hasattr(ccxt, ex_id):
            try:
                exchanges_dict[ex_id] = getattr(ccxt, ex_id)(params)
                logging.info(f"✅ {ex_id.upper()} 接口装载完毕")
            except: pass

async def get_global_targets():
    global_targets = []
    async def fetch_markets(ex_id, ex):
        try:
            markets = await ex.load_markets()
            tickers = await safe_api_request(ex, 'fetch_tickers')
            if not tickers: return
            is_dex = (ex_id == 'hyperliquid')
            
            for symbol, info in markets.items():
                if not info.get('active', True): continue
                if 'USDT' not in symbol and 'USDC' not in symbol and 'USD' not in symbol: continue 
                if symbol not in tickers: continue
                
                vol = tickers[symbol].get('quoteVolume', 0)
                if vol is None: vol = 0
                
                is_vip = any(vip in symbol.split('/')[0] for vip in VIP_ASSETS)
                threshold = DEX_MIN_VOLUME if is_dex else (VIP_MIN_VOLUME if is_vip else MIN_VOLUME_USDT)
                    
                if vol >= threshold:
                    global_targets.append({'exchange': ex, 'symbol': symbol})
        except: pass
    await asyncio.gather(*[fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()])
    return global_targets

def calc_true_range(df):
    """准确计算 True Range (TR) 向量"""
    prev_close = df['close'].shift(1)
    tr0 = abs(df['high'] - df['low'])
    tr1 = abs(df['high'] - prev_close)
    tr2 = abs(df['low'] - prev_close)
    return pd.concat([tr0, tr1, tr2], axis=1).max(axis=1)

async def check_structure(ex, symbol):
    """🔍 V28 ATR 动态自适应箱体识别"""
    try:
        # 获取120根线，保证计算ATR的数据充足
        bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, timeframe='1h', limit=120)
        if not bars or len(bars) < MIN_HISTORY + 2: return None
        
        df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        df['tr'] = calc_true_range(df)
        
        # 截取过去90根完整K线作为判断域 (不含当前未收盘的最后1根)
        box = df.iloc[-(MIN_HISTORY+1) : -1] 
        box_high, box_low = box['high'].max(), box['low'].min()
        box_height = box_high - box_low
        
        # 1. 计算全局 90 小时平均真实波幅 (ATR)
        atr_90 = box['tr'].mean()
        if atr_90 <= 0: return None
        
        # 2. 🔥 ATR 动态门槛：无论是黄金还是山寨币，箱体高度必须是其自身ATR的 1.5 到 4 倍
        if not (ATR_MULTIPLIER_MIN * atr_90 <= box_height <= ATR_MULTIPLIER_MAX * atr_90): 
            return None 
            
        upper_zone = box_high - (box_height * EDGE_ZONE_RATIO)
        lower_zone = box_low + (box_height * EDGE_ZONE_RATIO)
        
        touch_count, rejection_candles = 0, 0
        
        for index, row in box.iterrows():
            is_touch, is_rejection = False, False
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
        
        if touch_count < MIN_TOUCHES or rejection_candles < MIN_REJECTIONS: return None

        # 3. 收敛验证：末端 4 根 K 线的平均 TR 必须显著低于全局 ATR
        recent_4_atr = box.iloc[-4:]['tr'].mean()
        if recent_4_atr > atr_90 * SQUEEZE_FACTOR: return None

        return {'high': box_high, 'low': box_low, 'atr_90': atr_90}
    except: return None

async def radar_job():
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logging.info(f"📡 整点雷达扫描开启，共检测 {len(targets)} 个标的...")
                
                async def check_wrapper(ex, symbol, uid):
                    if uid in watchlist: return None
                    struct = await check_structure(ex, symbol)
                    if struct: return (ex, symbol, uid, struct)
                    return None

                tasks = [asyncio.create_task(check_wrapper(t['exchange'], t['symbol'], f"{t['exchange'].id}:{t['symbol']}")) for t in targets]
                results = await asyncio.gather(*tasks)
                
                count_new = 0
                now_utc8 = datetime.now(tz_utc_8)
                for res in results:
                    if res:
                        ex, symbol, uid, struct = res
                        expiry = now_utc8 + timedelta(hours=4) 
                        data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol, 
                                'high': struct['high'], 'low': struct['low'], 
                                'atr_90': struct['atr_90'], 'expiry': expiry}
                        watchlist[uid] = {'exchange': ex, 'symbol': symbol, 'high': struct['high'], 
                                          'low': struct['low'], 'atr_90': struct['atr_90'], 'expiry': expiry}
                        db_crud('add_watch', data)
                        count_new += 1
                if count_new > 0:
                    logging.info(f"🤫 威科夫雷达静默锁定 {count_new} 个高潜目标 (自适应ATR).")
        except Exception as e: logging.error(f"雷达扫描异常: {e}")
        # ==========================================
        # 🔥 核心升级：强行对齐下一个整点 + 15秒缓冲
        # ==========================================
        now_utc8 = datetime.now(tz_utc_8)
        # 算出下一个整点时间，并加上 15 秒 (给交易所生成K线留出时间)
        next_hour = (now_utc8 + timedelta(hours=1)).replace(minute=0, second=15, microsecond=0)
        # 计算需要休眠的精确秒数
        sleep_sec = (next_hour - now_utc8).total_seconds()
        logging.info(f"⏳ 雷达扫描完毕。进入休眠，等待下一次整点发车，倒计时: {int(sleep_sec)} 秒")
        await asyncio.sleep(sleep_sec) 

async def sniper_job():
    while True:
        start = time.time()
        if watchlist:
            tasks = []
            now_utc8 = datetime.now(tz_utc_8)
            for uid in list(watchlist.keys()):
                info = watchlist[uid]
                if now_utc8 > info['expiry'].replace(tzinfo=tz_utc_8):
                    del watchlist[uid]
                    db_crud('remove_watch', {'uid': uid})
                    continue
                tasks.append(asyncio.create_task(snip_target(uid, info)))
            await asyncio.gather(*tasks)
        await asyncio.sleep(max(30 - (time.time() - start), 1)) 

async def snip_target(uid, info):
    try:
        ex, symbol = info['exchange'], info['symbol']
        ticker = await safe_api_request(ex, 'fetch_ticker', symbol)
        if not ticker: return

        price = ticker['last']
        signal, break_price, direction, card_color = None, None, None, None
        
        if price > info['high']: 
            signal, break_price, direction, card_color = "🟢 向上突破", info['high'], 'up', 'green'
        elif price < info['low']: 
            signal, break_price, direction, card_color = "🔴 向下跌破", info['low'], 'down', 'red'
            
        if signal:
            logging.info(f"⚡ {symbol} 触发一阶突破，执行基座安检...")
            
            recent_bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', limit=12)
            if not recent_bars or len(recent_bars) < 11: return

            df = pd.DataFrame(recent_bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            df['tr'] = calc_true_range(df)
            
            # 取 [-10:-3] 这 7 根K线作为突破前的底座
            base_df = df.iloc[-10:-3]
            base_avg_tr = base_df['tr'].mean()
            atr_90 = info.get('atr_90', 999999)
            
            # 🔥 基座不能有过激波动，必须小于全局ATR的 1.2倍
            if base_avg_tr > atr_90 * BASE_CHECK_FACTOR:
                logging.warning(f"❌ {symbol} 基座剧烈震荡 (基座ATR超标)，过滤假突破。")
                del watchlist[uid]
                db_crud('remove_watch', {'uid': uid})
                return

            now_utc8 = datetime.now(tz_utc_8)
            breakout_time_str = now_utc8.strftime('%H:%M:%S')
            next_hour = (now_utc8 + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            close_ts = int(next_hour.timestamp() * 1000)
            
            # 🚀 瞬间投递飞书卡片队列 (非阻塞)
            md_content = f"**平台:** {ex.id.upper()}\n**品种:** {symbol}\n**现价:** {price}\n**突破关键位:** {break_price}\n\n---\n🕒 **警报时间:** {breakout_time_str}\n⏳ 预计确权: {next_hour.strftime('%H:%M')} 之后"
            card = build_feishu_card(f"{signal} 瞬时警报: {symbol}", md_content, card_color)
            await notify_queue.put(card)
            
            pending_data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol, 
                            'direction': direction, 'break_price': break_price, 
                            'close_ts': close_ts, 'breakout_time': breakout_time_str}
            pending_confirms[uid] = pending_data.copy()
            db_crud('add_confirm', pending_data)
            
            del watchlist[uid]
            db_crud('remove_watch', {'uid': uid})
    except: pass

async def confirmation_job():
    while True:
        try:
            if pending_confirms:
                now_utc8 = datetime.now(tz_utc_8)
                current_ts = int(now_utc8.timestamp() * 1000)
                
                for uid in list(pending_confirms.keys()):
                    item = pending_confirms[uid]
                    
                    if current_ts > item['close_ts'] + 60000:
                        ex, symbol = item['exchange'], item['symbol']
                        target_candle_start_ts = item['close_ts'] - 3600000
                        
                        candle_data = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', since=target_candle_start_ts, limit=1)
                        
                        if not candle_data: continue
                        if len(candle_data) > 0 and candle_data[0][0] == target_candle_start_ts:
                            close_price = candle_data[0][4]
                            break_price = item['break_price']
                            direction = item['direction']
                            
                            is_valid = (direction == 'up' and close_price > break_price) or \
                                       (direction == 'down' and close_price < break_price)
                            
                            if is_valid:
                                card_color = "green" if direction == 'up' else "red"
                                dir_text = "做多" if direction == 'up' else "做空"
                                md = f"**平台:** {ex.id.upper()}\n**品种:** {symbol}\n**方向:** **{dir_text}**\n**威科夫突破位:** {break_price}\n**1h收盘价:** {close_price}\n\n> 实体已有效越界，结构成立。"
                                card = build_feishu_card(f"✅ 确权有效: {symbol}", md, card_color)
                                await notify_queue.put(card) # 入列飞书
                            
                            del pending_confirms[uid]
                            db_crud('remove_confirm', {'uid': uid})
                        else:
                            if current_ts > item['close_ts'] + 300000:
                                del pending_confirms[uid]
                                db_crud('remove_confirm', {'uid': uid})
        except Exception as e: logging.error(f"确权异常: {e}")
        await asyncio.sleep(60)

async def main():
    print("==================================================")
    print("🚀 V28 威科夫量化狙击引擎 - 飞书异步并发版")
    print("算法: ATR(90) 动态自适应边界 + K线基座安检")
    print("==================================================")
    init_db()
    await init_exchanges()
    load_data_from_db()
    
    # 启动 4 个并行常驻任务：雷达、狙击、确权、外加专门的发信员
    await asyncio.gather(
        radar_job(), 
        sniper_job(), 
        confirmation_job(),
        feishu_worker()
    )

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n🛑 引擎安全停机。")