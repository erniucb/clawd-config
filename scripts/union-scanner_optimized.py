#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
万物并集猎手 V18.0 - 全面优化版
优化内容：
1. ✅ 配置外部化（config.json）
2. ✅ 数据库连接池优化（aiosqlite）
3. ✅ API 重试机制（backoff）
4. ✅ 自适应并发控制器
5. ✅ 结构化日志系统（JSON + 请求追踪）
6. ✅ 邮件队列系统（批量发送）
7. ✅ 错误分类与恢复策略
8. ✅ 性能监控（CPU、内存、网络）
"""

import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import aiosqlite
import logging
import smtplib
import time
import json
import os
import backoff
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, NamedTuple
import collections
import uuid
from pythonjsonlogger import jsonlogger
from dataclasses import dataclass
import psutil
import traceback
from enum import Enum

# ================= ⚙️ 配置管理 =================
DEFAULT_CONFIG = {
    "email": {
        "sender": "371398370@qq.com",
        "password": "hjqibancxrerbifb",
        "receiver": "371398370@qq.com",
        "smtp_server": "smtp.qq.com",
        "smtp_port": 587,
        "queue_enabled": True,
        "queue_batch_size": 5,
        "queue_interval_seconds": 10,
        "queue_max_retries": 3
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
        "adaptive_error_threshold": 0.3,
        "adaptive_success_threshold": 0.9,
        "adaptive_adjustment_window": 50,
        "adaptive_cooldown_seconds": 60
    },
    "retry": {
        "max_tries": 3,
        "max_time": 60,
        "exponential_base": 2
    },
    "logging": {
        "level": "INFO",
        "console_format": "%(asctime)s [%(levelname)s] %(message)s",
        "structured_logging": True
    },
    "monitoring": {
        "enabled": True,
        "log_interval_seconds": 300,
        "cpu_threshold": 80,
        "memory_threshold": 85
    },
    "exchanges": {
        "binance": {"enableRateLimit": True, "options": {"defaultType": "future"}, "timeout": 30000},
        "bybit":   {"enableRateLimit": True, "options": {"defaultType": "linear"}, "timeout": 30000},
        "bitget":  {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000},
        "bingx":   {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000},
        "msx":     {"enableRateLimit": True, "options": {"defaultType": "swap"},   "timeout": 30000}
    }
}

def load_config(config_path="/root/clawd/scripts/config.json"):
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
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

CONFIG = load_config()

# 提取配置
SENDER_EMAIL = CONFIG["email"]["sender"]
SENDER_PASSWORD = CONFIG["email"]["password"]
RECEIVER_EMAIL = CONFIG["email"]["receiver"]
SMTP_SERVER = CONFIG["email"]["smtp_server"]
SMTP_PORT = CONFIG["email"]["smtp_port"]
EMAIL_QUEUE_ENABLED = CONFIG["email"].get("queue_enabled", True)
EMAIL_QUEUE_BATCH_SIZE = CONFIG["email"].get("queue_batch_size", 5)
EMAIL_QUEUE_INTERVAL = CONFIG["email"].get("queue_interval_seconds", 10)
EMAIL_QUEUE_MAX_RETRIES = CONFIG["email"].get("queue_max_retries", 3)

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

MONITORING_ENABLED = CONFIG["monitoring"].get("enabled", True)
MONITORING_INTERVAL = CONFIG["monitoring"].get("log_interval_seconds", 300)
CPU_THRESHOLD = CONFIG["monitoring"].get("cpu_threshold", 80)
MEMORY_THRESHOLD = CONFIG["monitoring"].get("memory_threshold", 85)

# ================= 🎯 错误分类与恢复策略 =================
class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"
    API_LIMIT = "api_limit"
    EXCHANGE_ERROR = "exchange_error"
    DATABASE_ERROR = "database_error"
    EMAIL_ERROR = "email_error"
    UNKNOWN = "unknown"

class ErrorRecoveryStrategy(Enum):
    """错误恢复策略"""
    RETRY = "retry"  # 重试
    BACKOFF = "backoff"  # 退避等待
    SKIP = "skip"  # 跳过此操作
    RESTART_EXCHANGE = "restart_exchange"  # 重启交易所连接
    LOG_ONLY = "log_only"  # 仅记录日志

def classify_error(error: Exception) -> tuple[ErrorCategory, ErrorRecoveryStrategy]:
    """分类错误并返回恢复策略"""
    error_name = error.__class__.__name__
    error_msg = str(error).lower()

    # 网络错误
    if isinstance(error, (ConnectionError, TimeoutError)):
        return ErrorCategory.NETWORK, ErrorRecoveryStrategy.RETRY

    # API 限流
    if "rate limit" in error_msg or "too many requests" in error_msg:
        return ErrorCategory.API_LIMIT, ErrorRecoveryStrategy.BACKOFF

    # CCXT 网络错误
    if hasattr(error, '__class__'):
        if error_name in ['NetworkError', 'RequestTimeout']:
            return ErrorCategory.NETWORK, ErrorRecoveryStrategy.RETRY
        if error_name == 'RateLimitExceeded':
            return ErrorCategory.API_LIMIT, ErrorRecoveryStrategy.BACKOFF
        if error_name in ['ExchangeNotAvailable', 'DDoSProtection']:
            return ErrorCategory.EXCHANGE_ERROR, ErrorRecoveryStrategy.BACKOFF
        if error_name in ['InvalidNonce', 'AuthenticationError']:
            return ErrorCategory.EXCHANGE_ERROR, ErrorRecoveryStrategy.SKIP

    # 数据库错误
    if "database" in error_msg or "sqlite" in error_msg:
        return ErrorCategory.DATABASE_ERROR, ErrorRecoveryStrategy.RETRY

    # 邮件错误
    if "smtp" in error_msg or "email" in error_msg:
        return ErrorCategory.EMAIL_ERROR, ErrorRecoveryStrategy.LOG_ONLY

    return ErrorCategory.UNKNOWN, ErrorRecoveryStrategy.LOG_ONLY

# ================= 📊 性能监控 =================
class PerformanceMonitor:
    """性能监控器"""
    def __init__(self, interval_seconds: int = 300, cpu_threshold: float = 80, memory_threshold: float = 85):
        self.interval_seconds = interval_seconds
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._start_time = time.time()

        # 统计信息
        self.api_call_count = 0
        self.api_success_count = 0
        self.api_failure_count = 0

    async def start(self):
        """启动监控"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"性能监控启动", extra={'interval': self.interval_seconds})

    async def stop(self):
        """停止监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._log_stats()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error(f"性能监控异常", extra={'error': str(e)})
                await asyncio.sleep(self.interval_seconds)

    def _log_stats(self):
        """记录性能统计"""
        # CPU 和内存使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # 网络统计
        network = psutil.net_io_counters()

        # 运行时间
        uptime = time.time() - self._start_time
        uptime_hours = uptime / 3600

        # API 统计
        api_success_rate = self.api_success_count / self.api_call_count * 100 if self.api_call_count > 0 else 0

        stats = {
            'uptime_hours': round(uptime_hours, 2),
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'network_sent_mb': round(network.bytes_sent / (1024**2), 2),
            'network_recv_mb': round(network.bytes_recv / (1024**2), 2),
            'api_call_count': self.api_call_count,
            'api_success_count': self.api_success_count,
            'api_failure_count': self.api_failure_count,
            'api_success_rate': round(api_success_rate, 2)
        }

        # 警告检查
        warnings = []
        if cpu_percent > self.cpu_threshold:
            warnings.append(f"CPU使用率过高: {cpu_percent}%")
        if memory_percent > self.memory_threshold:
            warnings.append(f"内存使用率过高: {memory_percent}%")

        logger.info(f"性能统计", extra={**stats, 'warnings': warnings if warnings else None})

        if warnings:
            logger.warning(f"性能警告", extra={'warnings': warnings})

    def record_api_call(self, success: bool):
        """记录API调用"""
        self.api_call_count += 1
        if success:
            self.api_success_count += 1
        else:
            self.api_failure_count += 1

    def get_stats(self) -> Dict:
        """获取统计信息"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        uptime = time.time() - self._start_time

        return {
            'uptime_hours': round(uptime / 3600, 2),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'api_call_count': self.api_call_count,
            'api_success_rate': round(self.api_success_count / self.api_call_count * 100, 2) if self.api_call_count > 0 else 0
        }

# 全局性能监控器
performance_monitor = PerformanceMonitor(
    interval_seconds=MONITORING_INTERVAL,
    cpu_threshold=CPU_THRESHOLD,
    memory_threshold=MEMORY_THRESHOLD
)

# ================= 📝 结构化日志系统 =================
class StructuredFormatter(jsonlogger.JsonFormatter):
    """自定义结构化日志格式器"""
    def add_fields(self, log_record, record, message_dict):
        super(StructuredFormatter, self).add_fields(log_record, record, message_dict)
        log_record['logger'] = record.name
        log_record['level'] = record.levelname
        log_record['process_id'] = os.getpid()
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'exchange'):
            log_record['exchange'] = record.exchange
        if hasattr(record, 'symbol'):
            log_record['symbol'] = record.symbol
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_category'):
            log_record['error_category'] = record.error_category

logger = logging.getLogger('union_scanner')
logger.setLevel(getattr(logging, CONFIG["logging"]["level"]))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(CONFIG["logging"]["console_format"]))
logger.addHandler(console_handler)

if CONFIG["logging"].get("structured_logging", True):
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(StructuredFormatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
    logger.addHandler(file_handler)

class RequestContext:
    """请求追踪上下文管理器"""
    def __init__(self, exchange=None, symbol=None):
        self.request_id = str(uuid.uuid4())[:8]
        self.exchange = exchange
        self.symbol = symbol
        self.start_time = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        logger.debug(
            f"请求完成",
            extra={
                'request_id': self.request_id,
                'exchange': self.exchange,
                'symbol': self.symbol,
                'duration_ms': duration_ms
            }
        )

# ================= 📧 邮件队列系统 =================
@dataclass
class EmailTask:
    subject: str
    content: str
    retries: int = 0
    created_at: float = time.time()

class EmailQueue:
    """邮件队列系统"""
    def __init__(self, sender, password, receiver, smtp_server, smtp_port, batch_size=5, interval_seconds=10, max_retries=3):
        self.sender = sender
        self.password = password
        self.receiver = receiver
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.batch_size = batch_size
        self.interval_seconds = interval_seconds
        self.max_retries = max_retries

        self.queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

        self.total_queued = 0
        self.total_sent = 0
        self.total_failed = 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info(f"邮件队列系统启动", extra={'batch_size': self.batch_size})

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("邮件队列系统停止")

    async def enqueue(self, subject: str, content: str):
        email_task = EmailTask(subject=subject, content=content)
        await self.queue.put(email_task)
        self.total_queued += 1
        logger.debug(f"邮件加入队列", extra={'subject': subject, 'queue_size': self.queue.qsize()})

    async def _process_queue(self):
        while self._running:
            try:
                batch = []
                while len(batch) < self.batch_size and not self.queue.empty():
                    try:
                        email_task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                        batch.append(email_task)
                    except asyncio.TimeoutError:
                        break

                if not batch:
                    await asyncio.sleep(self.interval_seconds)
                    continue

                await self._send_batch(batch)
                await asyncio.sleep(self.interval_seconds)

            except Exception as e:
                category, strategy = classify_error(e)
                logger.error(
                    f"邮件队列处理异常",
                    extra={'error': str(e), 'error_category': category.value}
                )
                await asyncio.sleep(self.interval_seconds)

    async def _send_batch(self, batch: List[EmailTask]):
        for email_task in batch:
            try:
                await self._send_single_email(email_task)
                self.total_sent += 1
                self.queue.task_done()
            except Exception as e:
                email_task.retries += 1
                if email_task.retries < self.max_retries:
                    await self.queue.put(email_task)
                    category, strategy = classify_error(e)
                    logger.warning(
                        f"邮件发送失败，将重试",
                        extra={
                            'subject': email_task.subject,
                            'retries': email_task.retries,
                            'error': str(e),
                            'error_category': category.value
                        }
                    )
                else:
                    self.total_failed += 1
                    self.queue.task_done()
                    category, strategy = classify_error(e)
                    logger.error(
                        f"邮件发送最终失败",
                        extra={
                            'subject': email_task.subject,
                            'retries': email_task.retries,
                            'error': str(e),
                            'error_category': category.value
                        }
                    )

    async def _send_single_email(self, email_task: EmailTask):
        def sync_send():
            msg = MIMEText(email_task.content, 'plain', 'utf-8')
            msg['From'] = formataddr(["万物并集猎手", self.sender])
            msg['To'] = formataddr(["指挥官", self.receiver])
            msg['Subject'] = email_task.subject

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, self.receiver, msg.as_string())
            server.quit()

        await asyncio.to_thread(sync_send)
        logger.info(f"邮件发送成功", extra={'subject': email_task.subject})

    def get_stats(self) -> Dict:
        return {
            "total_queued": self.total_queued,
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "queue_size": self.queue.qsize()
        }

email_queue = EmailQueue(
    sender=SENDER_EMAIL,
    password=SENDER_PASSWORD,
    receiver=RECEIVER_EMAIL,
    smtp_server=SMTP_SERVER,
    smtp_port=SMTP_PORT,
    batch_size=EMAIL_QUEUE_BATCH_SIZE,
    interval_seconds=EMAIL_QUEUE_INTERVAL,
    max_retries=EMAIL_QUEUE_MAX_RETRIES
)

async def send_email(subject: str, content: str):
    if EMAIL_QUEUE_ENABLED:
        await email_queue.enqueue(subject, content)
    else:
        async def sync_send():
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['From'] = formataddr(["万物并集猎手", SENDER_EMAIL])
            msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
            msg['Subject'] = subject

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()
            logger.info(f"邮件发送成功", extra={'subject': subject})

        try:
            await asyncio.to_thread(sync_send)
        except Exception as e:
            category, strategy = classify_error(e)
            logger.error(f"邮件发送失败", extra={'subject': subject, 'error': str(e), 'error_category': category.value})

# ================= 🔄 API 重试机制 =================
def should_retry_api_error(e):
    category, strategy = classify_error(e)
    return strategy in [ErrorRecoveryStrategy.RETRY, ErrorRecoveryStrategy.BACKOFF]

def on_retry(details):
    logger.warning(
        f"API 请求失败，正在重试... "
        f"尝试 {details['tries']}/{RETRY_MAX_TRIES}, "
        f"等待 {details['wait']:.1f}秒"
    )

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
    """自适应并发控制器"""
    def __init__(self, max_concurrency, min_concurrency=5, max_adaptive_limit=15,
                 error_threshold=0.3, success_threshold=0.9, window_size=50, cooldown_seconds=60):
        self.max_concurrency = max_concurrency
        self.min_concurrency = min_concurrency
        self.max_adaptive_limit = max_adaptive_limit
        self.error_threshold = error_threshold
        self.success_threshold = success_threshold
        self.window_size = window_size
        self.cooldown_seconds = cooldown_seconds

        self.current_concurrency = max_concurrency
        self.request_history: collections.deque = collections.deque(maxlen=window_size)
        self.last_adjustment_time = 0
        self.semaphore: Optional[asyncio.Semaphore] = None

        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    async def initialize(self):
        self.semaphore = asyncio.Semaphore(self.current_concurrency)
        logger.info(f"自适应并发控制器初始化完成", extra={'current_concurrency': self.current_concurrency})

    def record_request(self, success: bool):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.request_history.append(success)
        if len(self.request_history) >= self.window_size:
            self._try_adjust_concurrency()

    def _try_adjust_concurrency(self):
        now = time.time()
        if now - self.last_adjustment_time < self.cooldown_seconds:
            return

        success_count = sum(1 for result in self.request_history if result)
        success_rate = success_count / len(self.request_history)

        if success_rate < (1 - self.error_threshold) and self.current_concurrency > self.min_concurrency:
            self.current_concurrency = max(self.min_concurrency, self.current_concurrency - 1)
            self.last_adjustment_time = now
            logger.warning(
                f"自适应降级: 成功率 {success_rate:.1%}",
                extra={'event': 'adaptive_downgrade', 'success_rate': success_rate}
            )
            self._update_semaphore()
        elif success_rate >= self.success_threshold and self.current_concurrency < self.max_adaptive_limit:
            self.current_concurrency = min(self.max_adaptive_limit, self.current_concurrency + 1)
            self.last_adjustment_time = now
            logger.info(
                f"自适应升级: 成功率 {success_rate:.1%}",
                extra={'event': 'adaptive_upgrade', 'success_rate': success_rate}
            )
            self._update_semaphore()

    def _update_semaphore(self):
        if self.semaphore:
            self.semaphore = asyncio.Semaphore(self.current_concurrency)

    def get_stats(self) -> Dict:
        success_count = sum(1 for result in self.request_history if result)
        success_rate = success_count / len(self.request_history) if self.request_history else 0
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "current_concurrency": self.current_concurrency
        }

adaptive_controller = AdaptiveConcurrencyController(
    max_concurrency=MAX_CONCURRENT_REQUESTS,
    min_concurrency=CONFIG["concurrency"].get("adaptive_min_concurrency", 5),
    max_adaptive_limit=CONFIG["concurrency"].get("adaptive_max_concurrency", 15),
    error_threshold=CONFIG["concurrency"].get("adaptive_error_threshold", 0.3),
    success_threshold=CONFIG["concurrency"].get("adaptive_success_threshold", 0.9),
    window_size=CONFIG["concurrency"].get("adaptive_adjustment_window", 50),
    cooldown_seconds=CONFIG["concurrency"].get("adaptive_cooldown_seconds", 60)
)

analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSIS)

# ================= 💾 数据库连接池 =================
class AsyncDBPool:
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS watchlist
                              (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, expiry TEXT)''')
            await db.execute('''CREATE TABLE IF NOT EXISTS alert_history
                              (uid TEXT PRIMARY KEY, last_alert TEXT)''')
            await db.commit()
        for _ in range(self.pool_size):
            conn = await aiosqlite.connect(self.db_path)
            await self.pool.put(conn)
        self._initialized = True
        logger.info(f"数据库连接池初始化完成", extra={'pool_size': self.pool_size})

    @asynccontextmanager
    async def get_connection(self):
        if not self._initialized:
            await self.initialize()
        conn = await self.pool.get()
        try:
            yield conn
        finally:
            await self.pool.put(conn)

    async def close_all(self):
        while not self.pool.empty():
            conn = await self.pool.get()
            await conn.close()
        self._initialized = False

db_pool = AsyncDBPool(DB_FILE, DB_POOL_SIZE)

async def init_db():
    await db_pool.initialize()

async def db_add_watchlist(uid, ex_id, symbol, high, low, expiry):
    async with db_pool.get_connection() as db:
        await db.execute(
            "REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, expiry) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, ex_id, symbol, high, low, expiry.isoformat())
        )
        await db.commit()

async def db_remove_watchlist(uid):
    async with db_pool.get_connection() as db:
        await db.execute("DELETE FROM watchlist WHERE uid=?", (uid,))
        await db.commit()

async def db_update_alert(uid, alert_time):
    async with db_pool.get_connection() as db:
        await db.execute(
            "REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)",
            (uid, alert_time.isoformat())
        )
        await db.commit()

# ================= 🌐 核心逻辑 =================
exchanges_dict = {}
watchlist = {}
alert_history = {}

async def init_exchanges():
    logger.info("正在初始化异步交易所联盟...")
    for ex_id, params in EXCHANGES_TO_LOAD.items():
        if hasattr(ccxt, ex_id):
            try:
                ex_class = getattr(ccxt, ex_id)
                exchanges_dict[ex_id] = ex_class(params)
                logger.info(f"异步加载成功", extra={'exchange': ex_id})
            except Exception as e:
                category, strategy = classify_error(e)
                logger.warning(f"初始化失败", extra={'exchange': ex_id, 'error': str(e), 'error_category': category.value})
    if not exchanges_dict:
        logger.error("无可用交易所，退出！")
        exit()

async def load_data_from_db():
    async with db_pool.get_connection() as db:
        async with db.execute("SELECT uid, last_alert FROM alert_history") as cursor:
            async for row in cursor:
                alert_history[row[0]] = datetime.fromisoformat(row[1])

        restored_count = 0
        now = datetime.now()
        async with db.execute("SELECT uid, exchange_id, symbol, high, low, expiry FROM watchlist") as cursor:
            async for row in cursor:
                uid, ex_id, symbol, high, low, expiry_str = row
                expiry = datetime.fromisoformat(expiry_str)
                if expiry <= now or ex_id not in exchanges_dict:
                    await db_remove_watchlist(uid)
                    continue
                watchlist[uid] = {
                    'exchange': exchanges_dict[ex_id], 'symbol': symbol,
                    'high': high, 'low': low, 'expiry': expiry
                }
                restored_count += 1

    logger.info(f"数据库恢复完成", extra={'restored_count': restored_count})

async def get_global_targets():
    logger.info("开始拉取全市场数据...")
    global_targets = []

    async def fetch_markets(ex_id, ex):
        @async_retry
        async def fetch_with_retry():
            return await ex.load_markets()

        try:
            with RequestContext(exchange=ex_id):
                markets = await fetch_with_retry()
                adaptive_controller.record_request(True)
                performance_monitor.record_api_call(True)
                count = 0
                for symbol, info in markets.items():
                    if not (symbol.endswith(':USDT') or symbol.endswith('/USDT')): continue
                    if not info.get('active', True): continue
                    vol = info.get('quoteVolume', 0)
                    if vol and vol > MIN_VOLUME_USDT:
                        global_targets.append({'exchange': ex, 'symbol': symbol, 'vol': vol})
                        count += 1
                logger.info(f"拉取市场数据完成", extra={'exchange': ex_id, 'count': count})
        except Exception as e:
            adaptive_controller.record_request(False)
            performance_monitor.record_api_call(False)
            category, strategy = classify_error(e)
            logger.warning(f"无法拉取市场数据", extra={'exchange': ex_id, 'error': str(e), 'error_category': category.value})

    tasks = [fetch_markets(ex_id, ex) for ex_id, ex in exchanges_dict.items()]
    await asyncio.gather(*tasks)

    global_targets = sorted(global_targets, key=lambda x: x['vol'], reverse=True)
    logger.info(f"全市场数据拉取完成", extra={'total_targets': len(global_targets)})
    return global_targets

async def check_structure(ex, symbol):
    async with adaptive_controller.semaphore:
        @async_retry
        async def fetch_with_retry():
            return await ex.fetch_ohlcv(symbol, timeframe='1h', limit=120)

        try:
            with RequestContext(exchange=ex.id, symbol=symbol):
                bars = await fetch_with_retry()
                adaptive_controller.record_request(True)
                performance_monitor.record_api_call(True)
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
            adaptive_controller.record_request(False)
            performance_monitor.record_api_call(False)
            category, strategy = classify_error(e)
            logger.debug(f"形态检测失败", extra={'exchange': ex.id, 'symbol': symbol, 'error': str(e), 'error_category': category.value})
            return None

async def radar_job():
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                logger.info(f"开始并发分析 K 线形态", extra={'target_count': len(targets)})

                tasks = []
                for target in targets:
                    ex = target['exchange']
                    symbol = target['symbol']
                    uid = f"{ex.id}:{symbol}"
                    if uid not in watchlist:
                        tasks.append(asyncio.create_task(process_single_target(ex, symbol, uid)))

                await asyncio.gather(*tasks)
                logger.info(f"本轮全域雷达并发扫描完成")

                # 打印统计
                stats = adaptive_controller.get_stats()
                logger.info(f"并发统计", extra=stats)
                email_stats = email_queue.get_stats()
                logger.info(f"邮件队列统计", extra=email_stats)
                perf_stats = performance_monitor.get_stats()
                logger.info(f"性能统计", extra=perf_stats)

        except Exception as e:
            category, strategy = classify_error(e)
            logger.error(f"雷达任务异常", extra={'error': str(e), 'error_category': category.value})

        await asyncio.sleep(RADAR_INTERVAL)

async def process_single_target(ex, symbol, uid):
    async with analysis_semaphore:
        struct = await check_structure(ex, symbol)
        if struct:
            expiry_time = datetime.now() + timedelta(hours=WATCHLIST_EXPIRY_HOURS)
            watchlist[uid] = {
                'exchange': ex, 'symbol': symbol, 'expiry': expiry_time,
                'high': struct['high'], 'low': struct['low']
            }
            await db_add_watchlist(uid, ex.id, symbol, struct['high'], struct['low'], expiry_time)

            logger.info(
                f"锁定目标",
                extra={
                    'exchange': ex.id,
                    'symbol': symbol,
                    'high': struct['high'],
                    'low': struct['low'],
                    'amp': struct['amp']
                }
            )
            asyncio.create_task(send_email(
                f"【并集发现】{symbol} 在 {ex.id.upper()} 收敛",
                f"平台: {ex.id.upper()}\n品种: {symbol}\n阻力: {struct['high']}\n支撑: {struct['low']}"
            ))

async def sniper_job():
    while True:
        start_time = time.time()

        if watchlist:
            tasks = []
            for uid in list(watchlist.keys()):
                info = watchlist[uid]
                ex = info['exchange']
                symbol = info['symbol']

                if datetime.now() > info['expiry']:
                    del watchlist[uid]
                    await db_remove_watchlist(uid)
                    logger.info(f"目标过期", extra={'uid': uid})
                    continue

                tasks.append(asyncio.create_task(snip_single_target(uid, ex, symbol, info)))

            await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        sleep_time = max(SNIPER_INTERVAL - elapsed, 1)
        await asyncio.sleep(sleep_time)

async def snip_single_target(uid, ex, symbol, info):
    async with adaptive_controller.semaphore:
        @async_retry
        async def fetch_ticker_with_retry():
            return await ex.fetch_ticker(symbol)

        try:
            with RequestContext(exchange=ex.id, symbol=symbol):
                ticker = await fetch_ticker_with_retry()
                adaptive_controller.record_request(True)
                performance_monitor.record_api_call(True)
                price = ticker['last']

                signal, break_price = None, None
                if price > info['high']: signal, break_price = "📈 向上突破", info['high']
                elif price < info['low']: signal, break_price = "📉 向下跌破", info['low']

                if signal:
                    logger.warning(
                        f"击杀确认",
                        extra={
                            'exchange': ex.id,
                            'symbol': symbol,
                            'signal': signal,
                            'price': price,
                            'break_price': break_price
                        }
                    )

                    if uid not in alert_history or datetime.now() - alert_history[uid] > timedelta(hours=ALERT_COOLDOWN_HOURS):
                        email_content = f"🚨 【并集突破警报】{symbol}\n\n平台: {ex.id.upper()}\n方向: {signal}\n现价: {price}\n突破位: {break_price}\n\n快去查看！"
                        asyncio.create_task(send_email(f"🚨 {signal} {symbol} ({ex.id.upper()})", email_content))

                        alert_history[uid] = datetime.now()
                        await db_update_alert(uid, datetime.now())

                        del watchlist[uid]
                        await db_remove_watchlist(uid)
        except Exception as e:
            adaptive_controller.record_request(False)
            performance_monitor.record_api_call(False)
            category, strategy = classify_error(e)
            logger.debug(f"价格查询失败", extra={'exchange': ex.id, 'symbol': symbol, 'error': str(e), 'error_category': category.value})

async def main():
    print("===================================================")
    print("🚀 万物并集猎手 V18.0 (全面优化版) 启动...")
    print("===================================================")

    await init_db()
    await adaptive_controller.initialize()
    await email_queue.start()
    await performance_monitor.start()
    await init_exchanges()
    await load_data_from_db()

    await asyncio.gather(
        radar_job(),
        sniper_job()
    )

    await email_queue.stop()
    await performance_monitor.stop()
    await db_pool.close_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("接收到退出指令，程序安全终止")
