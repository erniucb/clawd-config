import asyncio
import aiohttp
import ccxt.async_support as ccxt
import pandas as pd
import sqlite3
import logging
import time
from datetime import datetime, timedelta, timezone

# ================= ⚙️ V29 终极策略配置 =================
# 飞书机器人配置
FEISHU_APP_ID = 'cli_a9177b28e6f89cd4'
FEISHU_APP_SECRET = 'zJniiJUj8SHJbRO9DuiEYIBfHJv6gkfA'
FEISHU_USER_OPENID = 'ou_0058e09903092b62b45494eace8ab02f'

# 威科夫箱体 ATR 参数 (1H)
MIN_HISTORY = 90           
ATR_MULTIPLIER_MIN = 1.5   
ATR_MULTIPLIER_MAX = 4.0   
EDGE_ZONE_RATIO = 0.03     
SQUEEZE_FACTOR = 0.75      
BASE_CHECK_FACTOR = 1.2    

# 💥 VSA 成交量与 MTFA 趋势参数
VOL_BURST_MULTIPLIER = 1.5 # 突破瞬时投影量需 >= 1.5倍 20周期均量
MTFA_TIMEFRAME = '4h'      # 宏观趋势参考级别
EMA_FAST, EMA_MID, EMA_SLOW = 20, 50, 120 # 三均线参数
TANGLED_SPREAD = 0.02      # 均线粘合判定阈值 (2%)

# 过滤门槛
MIN_VOLUME_USDT = 3000000  
VIP_MIN_VOLUME = 10000     
DEX_MIN_VOLUME = 1000      

VIP_ASSETS = [
    'XAU', 'XAG', 'GOLD', 'SILVER', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD',    
    'TSLA', 'AAPL', 'NVDA', 'MSFT', 'AMZN', 'GOOG', 'COIN', 'MSTR', 
    'SPX', 'NAS', 'US500', 'US100', 'BTC', 'ETH', 'SOL', 'HYPE', 'PURR'
]

MIN_TOUCHES = 3            
MIN_REJECTIONS = 1         

DB_FILE = '/root/clawd/scripts/v29_wyckoff_ultimate.db' 
LOG_FILE = '/root/clawd/scripts/v29_engine.log'

tz_utc_8 = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

# ================= 🌐 交易所与流控 =================
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

sem_general = asyncio.Semaphore(20)  
sem_hyper = asyncio.Semaphore(2)     
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
                return await asyncio.wait_for(func(*args, **kwargs), timeout=10.0)
            except Exception as e:
                err_msg = str(e).lower()
                if '429' in err_msg or 'too many' in err_msg or 'timeout' in err_msg or 'network' in err_msg:
                    if i < retries - 1:
                        await asyncio.sleep((2 ** i) * 2)
                        continue
                return None
        return None

# ================= 💾 数据库防灾 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, 
                 atr_90 REAL, avg_vol_20 REAL, macro_state TEXT, allowed_dir TEXT, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pending_confirms
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, direction TEXT, break_price REAL, close_ts INTEGER, breakout_time TEXT)''')
    conn.commit()
    conn.close()

def db_crud(action, data=None):
    conn = sqlite3.connect(DB_FILE, timeout=10)
    c = conn.cursor()
    try:
        if action == 'add_watch':
            c.execute("REPLACE INTO watchlist VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['high'], data['low'], 
                       data['atr_90'], data['avg_vol_20'], data['macro_state'], data['allowed_dir'], data['expiry'].isoformat()))
        elif action == 'remove_watch':
            c.execute("DELETE FROM watchlist WHERE uid=?", (data['uid'],))
        elif action == 'add_confirm':
            c.execute("REPLACE INTO pending_confirms VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data['uid'], data['ex_id'], data['symbol'], data['direction'], data['break_price'], data['close_ts'], data['breakout_time']))
        elif action == 'remove_confirm':
            c.execute("DELETE FROM pending_confirms WHERE uid=?", (data['uid'],))
        conn.commit()
    except Exception as e: logging.error(f"DB Error: {e}")
    finally: conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        now_utc8 = datetime.now(tz_utc_8)
        for row in c.execute("SELECT * FROM watchlist").fetchall():
            uid, ex_id, symbol, high, low, atr_90, avg_vol_20, macro_state, allowed_dir, expiry_str = row
            expiry = datetime.fromisoformat(expiry_str)
            if expiry.replace(tzinfo=tz_utc_8) <= now_utc8 or ex_id not in exchanges_dict:
                db_crud('remove_watch', {'uid': uid})
                continue
            watchlist[uid] = {
                'exchange': exchanges_dict[ex_id], 'symbol': symbol, 'high': high, 'low': low, 
                'atr_90': atr_90, 'avg_vol_20': avg_vol_20, 'macro_state': macro_state, 'allowed_dir': allowed_dir, 'expiry': expiry
            }
        for row in c.execute("SELECT * FROM pending_confirms").fetchall():
            uid, ex_id, symbol, direction, break_price, close_ts, breakout_time = row
            if ex_id in exchanges_dict:
                pending_confirms[uid] = {
                    'exchange': exchanges_dict[ex_id], 'symbol': symbol, 'direction': direction, 
                    'break_price': break_price, 'close_ts': close_ts, 'breakout_time': breakout_time
                }
    except Exception: pass
    finally: conn.close()

# ================= 📧 飞书队列发信 =================
async def feishu_worker():
    """专职发信死循环，使用飞书 REST API 发送消息"""
    async with aiohttp.ClientSession() as session:
        while True:
            payload = await notify_queue.get()
            try:
                token = await get_feishu_token()
                if not token:
                    logging.error("无法获取飞书Token，跳过发送")
                    notify_queue.task_done()
                    continue
                
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

# ================= 🚀 核心逻辑与状态机 =================
async def init_exchanges():
    for ex_id, params in EXCHANGES_TO_LOAD.items():
        if hasattr(ccxt, ex_id):
            try: exchanges_dict[ex_id] = getattr(ccxt, ex_id)(params)
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
                if not info.get('active', True) or ('USDT' not in symbol and 'USDC' not in symbol and 'USD' not in symbol): continue
                if symbol not in tickers: continue
                vol = tickers[symbol].get('quoteVolume', 0) or 0
                is_vip = any(vip in symbol.split('/')[0] for vip in VIP_ASSETS)
                threshold = DEX_MIN_VOLUME if is_dex else (VIP_MIN_VOLUME if is_vip else MIN_VOLUME_USDT)
                if vol >= threshold: global_targets.append({'exchange': ex, 'symbol': symbol})
        except: pass
    await asyncio.gather(*[fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()])
    return global_targets

def calc_true_range(df):
    prev_close = df['close'].shift(1)
    return pd.concat([abs(df['high'] - df['low']), abs(df['high'] - prev_close), abs(df['low'] - prev_close)], axis=1).max(axis=1)

async def check_structure(ex, symbol):
    """🔍 V29 威科夫箱体 + MTFA状态机"""
    try:
        # 1. 检测 1H 威科夫箱体
        bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, timeframe='1h', limit=120)
        if not bars or len(bars) < MIN_HISTORY + 2: return None
        
        df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        df['tr'] = calc_true_range(df)
        
        box = df.iloc[-(MIN_HISTORY+1) : -1] 
        box_high, box_low = box['high'].max(), box['low'].min()
        box_height = box_high - box_low
        
        atr_90 = box['tr'].mean()
        if atr_90 <= 0 or not (ATR_MULTIPLIER_MIN * atr_90 <= box_height <= ATR_MULTIPLIER_MAX * atr_90): return None 
        
        upper_zone, lower_zone = box_high - (box_height * EDGE_ZONE_RATIO), box_low + (box_height * EDGE_ZONE_RATIO)
        touch_count, rejection_candles = 0, 0
        
        for _, row in box.iterrows():
            is_touch, is_rej = False, False
            o_p, c_p, h_p, l_p, body = row['open'], row['close'], row['high'], row['low'], abs(row['close'] - row['open'])
            if h_p >= upper_zone:
                is_touch = True
                if (h_p - max(o_p, c_p)) > body * 1.5: is_rej = True
            elif l_p <= lower_zone:
                is_touch = True
                if (min(o_p, c_p) - l_p) > body * 1.5: is_rej = True
            if is_touch: touch_count += 1
            if is_rej: rejection_candles += 1
        
        if touch_count < MIN_TOUCHES or rejection_candles < MIN_REJECTIONS: return None
        if box.iloc[-4:]['tr'].mean() > atr_90 * SQUEEZE_FACTOR: return None
        
        # 计算过去 20 根 1H 的平均基准量能
        avg_vol_20 = box['vol'].iloc[-20:].mean()

        # 2. 🔥 1H 箱体成立，拉取 4H 宏观数据判定状态
        bars_4h = await safe_api_request(ex, 'fetch_ohlcv', symbol, timeframe=MTFA_TIMEFRAME, limit=150)
        if not bars_4h: return None
        df_4h = pd.DataFrame(bars_4h, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        
        # 计算三均线
        close_4h = df_4h['close']
        ema20 = close_4h.ewm(span=EMA_FAST, adjust=False).mean().iloc[-1]
        ema50 = close_4h.ewm(span=EMA_MID, adjust=False).mean().iloc[-1]
        ema120 = close_4h.ewm(span=EMA_SLOW, adjust=False).mean().iloc[-1]
        
        ema_max, ema_min = max(ema20, ema50, ema120), min(ema20, ema50, ema120)
        spread = (ema_max - ema_min) / ema_min
        
        if spread < TANGLED_SPREAD:
            macro_state = f"🌀 4H均线极度粘合 (Spread: {spread*100:.1f}%)"
            allowed_dir = 'ALL' # 蓄力期，双向爆发皆可抓
        elif ema20 > ema50 > ema120:
            macro_state = "🟢 4H明确多头排列"
            allowed_dir = 'UP'  # 顺势，仅做多
        elif ema20 < ema50 < ema120:
            macro_state = "🔴 4H明确空头排列"
            allowed_dir = 'DOWN' # 顺势，仅做空
        else:
            macro_state = "⚠️ 4H趋势震荡无序"
            allowed_dir = 'ALL' 
            
        return {'high': box_high, 'low': box_low, 'atr_90': atr_90, 'avg_vol_20': avg_vol_20, 'macro_state': macro_state, 'allowed_dir': allowed_dir}
    except: return None

async def radar_job():
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logging.info(f"📡 整点雷达启动, 检测 {len(targets)} 个标的...")
                
                async def check_wrapper(ex, symbol, uid):
                    if uid in watchlist: return None
                    struct = await check_structure(ex, symbol)
                    if struct: return (ex, symbol, uid, struct)
                    return None

                results = await asyncio.gather(*[asyncio.create_task(check_wrapper(t['exchange'], t['symbol'], f"{t['exchange'].id}:{t['symbol']}")) for t in targets])
                
                count_new, now_utc8 = 0, datetime.now(tz_utc_8)
                for res in results:
                    if res:
                        ex, symbol, uid, struct = res
                        expiry = now_utc8 + timedelta(hours=4) 
                        data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol, 'high': struct['high'], 'low': struct['low'], 
                                'atr_90': struct['atr_90'], 'avg_vol_20': struct['avg_vol_20'], 
                                'macro_state': struct['macro_state'], 'allowed_dir': struct['allowed_dir'], 'expiry': expiry}
                        watchlist[uid] = data.copy()
                        watchlist[uid]['exchange'] = ex
                        db_crud('add_watch', data)
                        count_new += 1
                if count_new > 0: logging.info(f"🤫 锁定 {count_new} 个高潜目标 (MTFA状态已就绪).")
        except Exception as e: logging.error(f"雷达异常: {e}")

        # 精准时钟对齐
        now_utc8 = datetime.now(tz_utc_8)
        next_hour = (now_utc8 + timedelta(hours=1)).replace(minute=0, second=15, microsecond=0)
        logging.info(f"⏳ 雷达扫描完毕。进入休眠，等待下一次整点发车，倒计时: {int((next_hour - now_utc8).total_seconds())} 秒")
        await asyncio.sleep((next_hour - now_utc8).total_seconds())

async def sniper_job():
    while True:
        start = time.time()
        if watchlist:
            now_utc8 = datetime.now(tz_utc_8)
            tasks = []
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

        price, signal, break_price, direction, card_color = ticker['last'], None, None, None, None
        
        if price > info['high']: signal, break_price, direction, card_color = "🟢 向上突破", info['high'], 'up', 'green'
        elif price < info['low']: signal, break_price, direction, card_color = "🔴 向下跌破", info['low'], 'down', 'red'
            
        if signal:
            # 🛑 第一关：宏观 MTFA 趋势过滤
            if (direction == 'up' and info['allowed_dir'] == 'DOWN') or (direction == 'down' and info['allowed_dir'] == 'UP'):
                return # 逆大势信号，坚决丢弃 (保留在 watchlist 中等另一边突破)
            
            recent_bars = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', limit=12)
            if not recent_bars or len(recent_bars) < 11: return
            
            # 🛑 第二关：瞬时爆发量投影 (VSA)
            now_utc8 = datetime.now(tz_utc_8)
            current_vol = recent_bars[-1][5] # 最新一根还未收盘的 1H K线量能
            elapsed_minutes = now_utc8.minute + (now_utc8.second / 60.0)
            
            # 如果刚开局前2分钟量太小，或者投影量未达到基准均量的 1.5 倍，系统判定"主升浪动能暂未确认"
            if elapsed_minutes < 1: projected_vol = current_vol * 60 # 防除0
            else: projected_vol = current_vol * (60.0 / elapsed_minutes)
            
            if projected_vol < info['avg_vol_20'] * VOL_BURST_MULTIPLIER:
                return # 暂不发信，也不删除标的！下一个 30 秒轮询时只要量跟上了，瞬间触发。

            # 🛑 第三关：基座震荡安检
            df = pd.DataFrame(recent_bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            base_avg_tr = calc_true_range(df).iloc[-10:-3].mean()
            if base_avg_tr > info['atr_90'] * BASE_CHECK_FACTOR:
                del watchlist[uid]
                db_crud('remove_watch', {'uid': uid})
                return

            breakout_time_str = now_utc8.strftime('%H:%M:%S')
            next_hour = (now_utc8 + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            
            md_content = f"**标的:** {ex.id.upper()} - {symbol}\n**方向:** {signal} ({break_price})\n**现价:** {price}\n\n---\n📊 **MTFA (4H):** {info['macro_state']}\n🔥 **VSA 量能:** 已确认 (投影 > {VOL_BURST_MULTIPLIER}x 均量)\n🕒 **时间:** {breakout_time_str}"
            await notify_queue.put(build_feishu_card(f"🚀 {symbol} 主力点火", md_content, card_color))
            
            pending_data = {'uid': uid, 'ex_id': ex.id, 'symbol': symbol, 'direction': direction, 
                            'break_price': break_price, 'close_ts': int(next_hour.timestamp() * 1000), 'breakout_time': breakout_time_str}
            pending_confirms[uid] = pending_data.copy()
            db_crud('add_confirm', pending_data)
            
            del watchlist[uid]
            db_crud('remove_watch', {'uid': uid})
    except: pass

async def confirmation_job():
    while True:
        try:
            if pending_confirms:
                current_ts = int(datetime.now(tz_utc_8).timestamp() * 1000)
                for uid in list(pending_confirms.keys()):
                    item = pending_confirms[uid]
                    if current_ts > item['close_ts'] + 60000:
                        ex, symbol = item['exchange'], item['symbol']
                        target_start_ts = item['close_ts'] - 3600000
                        candle_data = await safe_api_request(ex, 'fetch_ohlcv', symbol, '1h', since=target_start_ts, limit=1)
                        
                        if not candle_data: continue
                        if len(candle_data) > 0 and candle_data[0][0] == target_start_ts:
                            close_price = candle_data[0][4]
                            is_valid = (item['direction'] == 'up' and close_price > item['break_price']) or (item['direction'] == 'down' and close_price < item['break_price'])
                            
                            if is_valid:
                                color = "green" if item['direction'] == 'up' else "red"
                                dir_text = "做多" if item['direction'] == 'up' else "做空"
                                await notify_queue.put(build_feishu_card(f"✅ 确权通过: {symbol}", f"**品种:** {symbol}\n**方向:** **{dir_text}**\n**1h收盘价:** {close_price}\n> 实体与量能同步越界，结构确立。", color))
                            
                            del pending_confirms[uid]
                            db_crud('remove_confirm', {'uid': uid})
                        elif current_ts > item['close_ts'] + 300000:
                            del pending_confirms[uid]
                            db_crud('remove_confirm', {'uid': uid})
        except: pass
        await asyncio.sleep(60)

async def main():
    print("==================================================")
    print("🚀 V29 终极引擎 - 威科夫 ATR + VSA爆量 + MTFA共振")
    print("==================================================")
    init_db()
    await init_exchanges()
    load_data_from_db()
    await asyncio.gather(radar_job(), sniper_job(), confirmation_job(), feishu_worker())

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n🛑 安全停机。")