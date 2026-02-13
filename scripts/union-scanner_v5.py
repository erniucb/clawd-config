import asyncio
import ccxt.async_support as ccxt  # 🔥 核心升级：引入 CCXT 的异步引擎
import pandas as pd
import aiosqlite  # ✅ 升级：使用 aiosqlite 替代 sqlite3
import logging
import smtplib
import time
import json
import os
import backoff  # ✅ 升级：API 重试机制
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
import collections

# ================= ⚙️ 配置管理 =================
DEFAULT_CONFIG = {
    "email": {
        "sender": "371398370@qq.com",
        "password": "hjqibancxrerbifb",
        "receiver": "371398370@qq.com",
        "smtp_server": "smtp.qq.com",
        "smtp_port": 587
    },
    "scanning": {
        "min_history": 90,
        "max_amplitude": 0.10,
        "squeeze_factor": 0.75,
        "min_volume_usdt": 5000000,
        "radar_interval_seconds": 3600,
        "sniper_interval_seconds": 60,
        "watchlist_expiry_hours": 4,
        "alert_cooldown_hours": 1
    },
    "database": {
        "path": "/root/clawd/scripts/hunter_data.db",
        "log_path": "/root/clawd/scripts/hunter_run.log",
        "pool_size": 5
    },
    "concurrency": {
        "max_concurrent_requests": 10,
        "max_concurrent_analysis": 20,
        "adaptive_enabled": True,
        "adaptive_min_concurrency": 5,
        "adaptive_max_concurrency": 15,
        "adaptive_error_threshold": 0.3,  # 30% 错误率触发降级
        "adaptive_success_threshold": 0.9,  # 90% 成功率触发升级
        "adaptive_adjustment_window": 50,  # 最近 50 次请求作为评估窗口
        "adaptive_cooldown_seconds": 60  # 调整后冷却时间
    },
    "retry": {
        "max_tries": 3,
        "max_time": 60,
        "exponential_base": 2
    },
    "exchanges": {
        "binance": {"enableRateLimit": True, "options": {"defaultType": "future"}, "timeout": 30000},
        "bybit":   {"enableRateLimit": True, "options": {"defaultType": "linear"}, "timeout": 30000},
        "bitget":  {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000},
        "bingx":   {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000},
        "msx":     {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000}
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s [%(levelname)s] %(message)s"
    }
}

def load_config(config_path="/root/clawd/scripts/config.json"):
    """加载配置文件，如果不存在则使用默认配置"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并配置（默认值 + 配置文件）
                def deep_merge(default, override):
                    result = default.copy()
                    for key, value in override.items():
                        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                            result[key] = deep_merge(result[key], value)
                        else:
                            result[key] = value
                    return result
                return deep_merge(DEFAULT_CONFIG, config)
        except Exception as e:
            logging.warning(f"⚠️ 配置文件加载失败，使用默认配置: {e}")
            return DEFAULT_CONFIG
    else:
        logging.info("📝 配置文件不存在，使用默认配置")
        return DEFAULT_CONFIG

# 加载配置
CONFIG = load_config()

# 从配置中提取常用变量（保持向后兼容）
SENDER_EMAIL = CONFIG["email"]["sender"]
SENDER_PASSWORD = CONFIG["email"]["password"]
RECEIVER_EMAIL = CONFIG["email"]["receiver"]
SMTP_SERVER = CONFIG["email"]["smtp_server"]
SMTP_PORT = CONFIG["email"]["smtp_port"]

MIN_HISTORY = CONFIG["scanning"]["min_history"]
MAX_AMPLITUDE = CONFIG["scanning"]["max_amplitude"]
SQUEEZE_FACTOR = CONFIG["scanning"]["squeeze_factor"]
MIN_VOLUME_USDT = CONFIG["scanning"]["min_volume_usdt"]
RADAR_INTERVAL = CONFIG["scanning"]["radar_interval_seconds"]
SNIPER_INTERVAL = CONFIG["scanning"]["sniper_interval_seconds"]
WATCHLIST_EXPIRY_HOURS = CONFIG["scanning"]["watchlist_expiry_hours"]
ALERT_COOLDOWN_HOURS = CONFIG["scanning"]["alert_cooldown_hours"]

DB_FILE = CONFIG["database"]["path"]
LOG_FILE = CONFIG["database"]["log_path"]
DB_POOL_SIZE = CONFIG["database"].get("pool_size", 5)

MAX_CONCURRENT_REQUESTS = CONFIG["concurrency"]["max_concurrent_requests"]
MAX_CONCURRENT_ANALYSIS = CONFIG["concurrency"]["max_concurrent_analysis"]

RETRY_MAX_TRIES = CONFIG["retry"].get("max_tries", 3)
RETRY_MAX_TIME = CONFIG["retry"].get("max_time", 60)

EXCHANGES_TO_LOAD = CONFIG["exchanges"]

# ================= 📝 专业日志系统 =================
logging.basicConfig(
    level=getattr(logging, CONFIG["logging"]["level"]),
    format=CONFIG["logging"]["format"],
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================= 🔄 API 重试机制 =================
def should_retry_api_error(e):
    """判断是否应该重试的 API 错误"""
    # 网络相关错误
    if isinstance(e, (ConnectionError, TimeoutError)):
        return True
    # CCXT 特定错误
    if hasattr(e, '__class__'):
        error_name = e.__class__.__name__
        # 网络超时、速率限制、服务不可用
        retryable_errors = [
            'NetworkError',
            'RequestTimeout',
            'RateLimitExceeded',
            'ExchangeNotAvailable',
            'DDoSProtection'
        ]
        if any(err in error_name for err in retryable_errors):
            return True
    return False

def on_retry(details):
    """重试时的回调"""
    logging.warning(
        f"🔄 API 请求失败，正在重试... "
        f"尝试 {details['tries']}/{RETRY_MAX_TRIES}, "
        f"等待 {details['wait']:.1f}秒, "
        f"错误: {details['exception']}"
    )

# 创建通用的异步重试装饰器
async_retry = backoff.on_exception(
    backoff.expo,
    Exception,
    max_tries=RETRY_MAX_TRIES,
    max_time=RETRY_MAX_TIME,
    giveup=lambda e: not should_retry_api_error(e),
    on_backoff=on_retry
)

# ================= 🧠 自适应并发控制器 =================
class AdaptiveConcurrencyController:
    """自适应并发控制器 - 根据网络状况动态调整并发数"""
    def __init__(
        self,
        max_concurrency: int,
        min_concurrency: int = 5,
        max_adaptive_limit: int = 15,
        error_threshold: float = 0.3,
        success_threshold: float = 0.9,
        window_size: int = 50,
        cooldown_seconds: int = 60
    ):
        self.max_concurrency = max_concurrency
        self.min_concurrency = min_concurrency
        self.max_adaptive_limit = max_adaptive_limit
        self.error_threshold = error_threshold
        self.success_threshold = success_threshold
        self.window_size = window_size
        self.cooldown_seconds = cooldown_seconds

        # 当前并发数
        self.current_concurrency = max_concurrency

        # 请求历史（True=成功, False=失败）
        self.request_history: collections.deque = collections.deque(maxlen=window_size)

        # 冷却时间
        self.last_adjustment_time = 0

        # 信号量
        self.semaphore: Optional[asyncio.Semaphore] = None

        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    async def initialize(self):
        """初始化信号量"""
        self.semaphore = asyncio.Semaphore(self.current_concurrency)
        logging.info(f"🎛️ 自适应并发控制器初始化完成 (当前: {self.current_concurrency}, 范围: {self.min_concurrency}-{self.max_adaptive_limit})")

    def record_request(self, success: bool):
        """记录请求结果"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.request_history.append(success)

        # 尝试调整并发数
        if len(self.request_history) >= self.window_size:
            self._try_adjust_concurrency()

    def _try_adjust_concurrency(self):
        """尝试调整并发数"""
        now = time.time()

        # 检查冷却时间
        if now - self.last_adjustment_time < self.cooldown_seconds:
            return

        # 计算成功率
        success_count = sum(1 for result in self.request_history if result)
        success_rate = success_count / len(self.request_history)

        # 错误率过高，降低并发
        if success_rate < (1 - self.error_threshold) and self.current_concurrency > self.min_concurrency:
            self.current_concurrency = max(self.min_concurrency, self.current_concurrency - 1)
            self.last_adjustment_time = now
            logging.warning(
                f"📉 自适应降级: 成功率 {success_rate:.1%} < {(1-self.error_threshold):.1%}, "
                f"并发数从 {self.current_concurrency+1} 降至 {self.current_concurrency}"
            )
            self._update_semaphore()

        # 成功率很高，尝试提高并发
        elif success_rate >= self.success_threshold and self.current_concurrency < self.max_adaptive_limit:
            self.current_concurrency = min(self.max_adaptive_limit, self.current_concurrency + 1)
            self.last_adjustment_time = now
            logging.info(
                f"📈 自适应升级: 成功率 {success_rate:.1%} >= {self.success_threshold:.1%}, "
                f"并发数从 {self.current_concurrency-1} 升至 {self.current_concurrency}"
            )
            self._update_semaphore()

    def _update_semaphore(self):
        """更新信号量"""
        if self.semaphore:
            # 替换信号量
            self.semaphore = asyncio.Semaphore(self.current_concurrency)

    async def acquire(self):
        """获取并发许可"""
        if self.semaphore:
            return await self.semaphore.acquire()
        return True

    def release(self):
        """释放并发许可"""
        if self.semaphore:
            self.semaphore.release()

    def get_stats(self) -> Dict:
        """获取统计信息"""
        success_count = sum(1 for result in self.request_history if result)
        success_rate = success_count / len(self.request_history) if self.request_history else 0

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "current_concurrency": self.current_concurrency,
            "min_concurrency": self.min_concurrency,
            "max_concurrency": self.max_adaptive_limit
        }

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# ================= 🌐 异步交易所池 =================
exchanges_dict = {}
watchlist = {}
alert_history = {}

# 初始化自适应并发控制器
adaptive_config = CONFIG["concurrency"]
adaptive_controller = AdaptiveConcurrencyController(
    max_concurrency=MAX_CONCURRENT_REQUESTS,
    min_concurrency=adaptive_config.get("adaptive_min_concurrency", 5),
    max_adaptive_limit=adaptive_config.get("adaptive_max_concurrency", 15),
    error_threshold=adaptive_config.get("adaptive_error_threshold", 0.3),
    success_threshold=adaptive_config.get("adaptive_success_threshold", 0.9),
    window_size=adaptive_config.get("adaptive_adjustment_window", 50),
    cooldown_seconds=adaptive_config.get("adaptive_cooldown_seconds", 60)
)

analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSIS)

# ================= 💾 aiosqlite 连接池管理 =================
class AsyncDBPool:
    """异步数据库连接池管理器"""
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def initialize(self):
        """初始化连接池"""
        if self._initialized:
            return

        # 创建表结构
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS watchlist
                              (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, expiry TEXT)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS alert_history
                              (uid TEXT PRIMARY KEY, last_alert TEXT)''')
            await db.commit()

        # 预创建连接池
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.db_path)
            await self.pool.put(conn)

        self._initialized = True
        logging.info(f"✅ 数据库连接池初始化完成 (池大小: {self.pool_size})")

    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        if not self._initialized:
            await self.initialize()

        conn = await self.pool.get()
        try:
            yield conn
        finally:
            await self.pool.put(conn)

    async def close_all(self):
        """关闭所有连接"""
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()
        self._initialized = False

# 全局数据库连接池
db_pool = AsyncDBPool(DB_FILE, DB_POOL_SIZE)

# ================= 💾 异步数据库操作 =================
async def init_db():
    """初始化数据库（已迁移到连接池）"""
    await db_pool.initialize()

async def db_add_watchlist(uid, ex_id, symbol, high, low, expiry):
    """添加/更新 watchlist"""
    async with db_pool.get_connection() as db:
        await db.execute(
            "REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, expiry) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, ex_id, symbol, high, low, expiry.isoformat())
        )
        await db.commit()

async def db_remove_watchlist(uid):
    """删除 watchlist"""
    async with db_pool.get_connection() as db:
        await db.execute("DELETE FROM watchlist WHERE uid=?", (uid,))
        await db.commit()

async def db_update_alert(uid, alert_time):
    """更新 alert_history"""
    async with db_pool.get_connection() as db:
        await db.execute(
            "REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)",
            (uid, alert_time.isoformat())
        )
        await db.commit()

async def load_data_from_db():
    """从数据库加载监控列表和提醒历史"""
    async with db_pool.get_connection() as db:
        # 加载提醒历史
        async with db.execute("SELECT uid, last_alert FROM alert_history") as cursor:
            async for row in cursor:
                alert_history[row[0]] = datetime.fromisoformat(row[1])

        # 加载监控列表
        restored_count = 0
        now = datetime.now()
        async with db.execute("SELECT uid, exchange_id, symbol, high, low, expiry FROM watchlist") as cursor:
            async for row in cursor:
                uid, ex_id, symbol, high, low, expiry_str = row
                expiry = datetime.fromisoformat(expiry_str)
                if expiry <= now or ex_id not in exchanges_dict:
                    # 过期或交易所不存在，删除
                    await db_remove_watchlist(uid)
                    continue
                watchlist[uid] = {
                    'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                    'high': high, 'low': low, 'expiry': expiry
                }
                restored_count += 1

    logging.info(f"🔄 数据库恢复完成: {restored_count} 个盯盘任务.")

# ================= 📧 邮件系统 (放入后台线程，不阻塞主循环，带重试) =================
@async_retry
async def sync_send_email_with_retry(subject, content):
    """带重试机制的同步邮件发送"""
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = formataddr(["万物并集猎手", SENDER_EMAIL])
    msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
    msg['Subject'] = subject

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    logging.info(f"📧 邮件已发送: {subject}")

async def send_email(subject, content):
    """异步包装器：让邮件发送在独立线程执行，绝对不卡顿盯盘"""
    try:
        await asyncio.to_thread(sync_send_email_with_retry, subject, content)
    except Exception as e:
        logging.error(f"❌ 邮件发送最终失败: {e}")

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

    # 并发获取所有交易所的市场数据（带重试）
    async def fetch_markets(ex_id, ex):
        @async_retry
        async def fetch_with_retry():
            return await ex.load_markets()

        try:
            markets = await fetch_with_retry()
            adaptive_controller.record_request(True)  # 记录成功
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
            adaptive_controller.record_request(False)  # 记录失败
            logging.warning(f"  - ⚠️ 无法拉取 {ex_id.upper()}: {e}")

    # 同时发车！
    tasks = [fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()]
    await asyncio.gather(*tasks)

    global_targets = sorted(global_targets, key=lambda x: x['vol'], reverse=True)
    return global_targets

async def check_structure(ex, symbol):
    """并发形态检测（带重试 + 自适应并发）"""
    async with adaptive_controller.semaphore:  # 使用自适应并发控制器
        @async_retry
        async def fetch_with_retry():
            return await ex.fetch_ohlcv(symbol, timeframe='1h', limit=120)

        try:
            bars = await fetch_with_retry()
            adaptive_controller.record_request(True)  # 记录成功
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
        except Exception as e:
            adaptive_controller.record_request(False)  # 记录失败
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

                # 打印自适应并发统计
                stats = adaptive_controller.get_stats()
                logging.info(f"📊 并发统计: 成功率 {stats['success_rate']:.1%}, "
                          f"当前并发 {stats['current_concurrency']}/{stats['max_concurrency']}, "
                          f"总请求 {stats['total_requests']}")

        except Exception as e:
            logging.error(f"雷达任务异常: {e}")

        # 睡一小时，再去扫
        await asyncio.sleep(RADAR_INTERVAL)

async def process_single_target(ex, symbol, uid):
    """处理单个标的的回调函数"""
    async with analysis_semaphore:  # 限制并发分析数
        struct = await check_structure(ex, symbol)
        if struct:
            expiry_time = datetime.now() + timedelta(hours=WATCHLIST_EXPIRY_HOURS)
            watchlist[uid] = {
                'exchange': ex, 'symbol': symbol, 'expiry': expiry_time,
                'high': struct['high'], 'low': struct['low']
            }
            await db_add_watchlist(uid, ex.id, symbol, struct['high'], struct['low'], expiry_time)

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
                    await db_remove_watchlist(uid)
                    logging.info(f"🗑️ 目标过期: {uid}")
                    continue

                # 派发并发盯盘任务
                tasks.append(asyncio.create_task(snip_single_target(uid, ex, symbol, info)))

            await asyncio.gather(*tasks)

        # 精确的 60 秒节拍器补偿
        elapsed = time.time() - start_time
        sleep_time = max(SNIPER_INTERVAL - elapsed, 1) # 至少睡 1 秒防死循环
        await asyncio.sleep(sleep_time)

async def snip_single_target(uid, ex, symbol, info):
    """并发查询最新价，判断突破（带重试）"""
    async with adaptive_controller.semaphore:
        @async_retry
        async def fetch_ticker_with_retry():
            return await ex.fetch_ticker(symbol)

        try:
            # 获取最新价 (走网络请求，但被 async 挂起，不会阻塞别人)
            ticker = await fetch_ticker_with_retry()
            adaptive_controller.record_request(True)  # 记录成功
            price = ticker['last']

            signal, break_price = None, None
            if price > info['high']: signal, break_price = "📈 向上突破", info['high']
            elif price < info['low']: signal, break_price = "📉 向下跌破", info['low']

            if signal:
                logging.warning(f"🚀 【击杀确认】 {ex.id.upper()} 的 {symbol} 触发突破！现价: {price}")

                if uid not in alert_history or datetime.now() - alert_history[uid] > timedelta(hours=ALERT_COOLDOWN_HOURS):
                    email_content = f"🚨 【并集突破警报】{symbol}\n\n平台: {ex.id.upper()}\n方向: {signal}\n现价: {price}\n突破位: {break_price}\n\n快去查看！"

                    # 异步发邮件
                    asyncio.create_task(send_email(f"🚨 {signal} {symbol} ({ex.id.upper()})", email_content))

                    alert_history[uid] = datetime.now()
                    await db_update_alert(uid, datetime.now())

                    del watchlist[uid]
                    await db_remove_watchlist(uid)
        except Exception as e:
            adaptive_controller.record_request(False)  # 记录失败
            pass # 网络抖动，忽略，等下一个 60 秒

async def main():
    print("===================================================")
    print("🚀 万物并集猎手 V15.0 (自适应并发版) 启动...")
    print("===================================================")

    await init_db()
    await adaptive_controller.initialize()
    await init_exchanges()
    await load_data_from_db()

    # 🔥 见证奇迹的时刻：雷达和狙击手作为两个独立的并发协程同时运行！
    # 互不干扰，雷达扫得再慢，狙击手也会准时在第 60 秒开枪。
    await asyncio.gather(
        radar_job(),
        sniper_job()
    )

    # 清理连接池
    await db_pool.close_all()

if __name__ == "__main__":
    try:
        # 启动 Python 异步事件循环
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 接收到退出指令，程序安全终止。")
