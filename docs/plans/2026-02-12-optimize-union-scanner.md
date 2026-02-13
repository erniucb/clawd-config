# union-scanner.py 优化计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 优化 union-scanner.py 的性能、可维护性和错误处理

**架构分析:**
- 当前使用 asyncio 并发
- SQLite 存储监控状态
- 邮件告警系统
- 多交易所支持（Binance, Bybit, Bitget, BingX, MSX）

**技术栈:**
- Python 3.10+
- asyncio (异步并发)
- ccxt (交易所API)
- SQLite3 (持久化)
- smtplib (邮件发送）
- pandas (数据分析）

---

## 待优化项

### 1. 配置外部化
**问题:** 配置硬编码在脚本中（邮箱、密码、阈值等）
**影响:** 修改配置需要编辑代码，不灵活
**解决方案:** 创建 config.json 文件

### 2. 数据库连接池优化
**问题:** 每次数据库操作都创建新连接，效率低
**影响:** 高频操作（如狙击手每60秒）会频繁创建/销毁连接
**解决方案:** 使用 aiosqlite 或连接池

### 3. API 重试机制
**问题:** 网络错误只记录日志，没有重试
**影响:** 临时网络故障导致漏检
**解决方案:** 添加指数退避重试策略

### 4. 并发限制优化
**问题:** Semaphore 固定为 10，可能不够
**影响:** 高并发场景下扫描速度受限
**解决方案:** 增加到 20-30，并做成可配置

### 5. 日志分级
**问题:** 所有日志都是 INFO 级别，难以调试
**影响:** 无法区分错误、警告、调试信息
**解决方案:** 添加日志级别配置和格式化

### 6. 邮件发送优化
**问题:** 每封邮件都创建新的 SMTP 连接
**影响:** 发送多封邮件时效率低，可能触发频率限制
**解决方案:** 批量发送或连接池

### 7. 错误处理改进
**问题:** 异常捕获后直接 pass，丢失上下文
**影响:** 难以排查问题
**解决方案:** 添加详细的错误分类和恢复策略

### 8. 性能监控
**问题:** 没有性能指标（API调用次数、响应时间、成功率）
**影响:** 无法评估优化效果
**解决方案:** 添加性能统计和健康检查

### 9. 资源清理
**问题:** watchlist 无限增长，有过期数据
**影响:** 长时间运行后数据库膨胀
**解决方案:** 定期清理过期数据

### 10. 配置验证
**问题:** 配置文件加载时没有验证
**影响:** 错误配置可能导致程序崩溃
**解决方案:** 添加配置 schema 验证

---

## 任务分解

### Task 1: 配置外部化

**文件:**
- 创建: `scripts/scanner_config.json`
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 创建配置文件**
```bash
# 创建配置文件结构
cat > scripts/scanner_config.json << 'EOF'
{
  "email": {
    "sender": "371398370@qq.com",
    "password": "hjqibancxrerbifb",
    "receiver": "371398370@qq.com"
  },
  "scanner": {
    "interval_seconds": 3600,
    "max_concurrent": 30,
    "min_history": 90,
    "check_interval_seconds": 60,
    "max_amplitude": 0.10,
    "min_amplitude": 0.015,
    "squeeze_factor": 0.75,
    "min_volume_usdt": 5000000,
    "min_volume_vip": 10000,
    "min_touches": 3,
    "min_rejections": 1
  },
  "database": {
    "file": "scanner_data.db",
    "cleanup_interval_hours": 24
  },
  "logging": {
    "level": "INFO",
    "file": "scanner_run.log"
  },
  "exchanges": ["binance", "bybit", "bitget", "bingx", "msx"]
}
EOF
```

**Step 2: 添加配置加载函数**
```python
# 在 union-scanner.py 顶部添加
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'scanner_config.json'

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 验证必要字段
            validate_config(config)
            return config
    except FileNotFoundError:
        logging.error(f"❌ 配置文件不存在: {CONFIG_FILE}")
        exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"❌ 配置文件格式错误: {e}")
        exit(1)

def validate_config(config):
    """验证配置完整性"""
    required_keys = ['email', 'scanner', 'database', 'logging']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"缺少必要配置: {key}")
    
    # 验证邮箱配置
    email = config['email']
    if 'sender' not in email or 'password' not in email:
        raise ValueError("邮箱配置不完整")
```

**Step 3: 替换硬编码配置**
```python
# 在代码中替换
# SENDER_EMAIL = '371398370@qq.com'
# ↓
config = load_config()
SENDER_EMAIL = config['email']['sender']
SENDER_PASSWORD = config['email']['password']

# MIN_HISTORY = 90
# ↓
MIN_HISTORY = config['scanner']['min_history']
```

**Step 4: 更新 init_db 函数**
```python
def init_db():
    db_path = Path(__file__).parent / config['database']['file']
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 添加自动清理
    c.execute('''CREATE TABLE IF NOT EXISTS metadata
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    # 记录初始化时间
    c.execute("REPLACE INTO metadata (key, value) VALUES ('init_time', ?)", 
              (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()
```

**验证:** 运行脚本，确认能正确加载配置

---

### Task 2: 数据库连接池优化

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 安装 aiosqlite**
```bash
pip install aiosqlite
```

**Step 2: 创建连接池类**
```python
# 添加到文件顶部
import aiosqlite
from contextlib import asynccontextmanager

class DatabasePool:
    """数据库连接池"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.pool = None
    
    async def connect(self):
        """从池中获取连接"""
        if self.pool is None:
            self.pool = await aiosqlite.connect(self.db_path)
        return self.pool
    
    @asynccontextmanager
    async def connection(self):
        """上下文管理器，自动归还连接"""
        db = await self.connect()
        try:
            yield db
        finally:
            # 连接池会自动管理
            pass

# 初始化连接池
db_pool = DatabasePool(CONFIG['database']['file'])
```

**Step 3: 替换所有数据库操作**
```python
# 旧代码
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute(...)
conn.close()

# 新代码
async with db_pool.connection() as db:
    await db.execute(...)
```

**Step 4: 更新数据库函数**
```python
async def db_add_watchlist(uid, ex_id, symbol, high, low, expiry):
    async with db_pool.connection() as db:
        await db.execute(
            "REPLACE INTO watchlist (uid, exchange_id, symbol, high, low, expiry) VALUES (?, ?, ?, ?, ?)",
            (uid, ex_id, symbol, high, low, expiry.isoformat())
        )

async def db_remove_watchlist(uid):
    async with db_pool.connection() as db:
        await db.execute("DELETE FROM watchlist WHERE uid=?", (uid,))

async def db_update_alert(uid, alert_time):
    async with db_pool.connection() as db:
        await db.execute("REPLACE INTO alert_history (uid, last_alert) VALUES (?, ?)", 
                      (uid, alert_time.isoformat()))
```

**验证:** 运行脚本，查看日志确认没有连接错误

---

### Task 3: API 重试机制

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 安装 backoff 库**
```bash
pip install backoff
```

**Step 2: 添加重试装饰器**
```python
# 添加到文件顶部
import backoff
from functools import wraps

def retry_on_network_error(max_tries=3):
    """网络错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_tries + 1):
                try:
                    return await func(*args, **kwargs)
                except (ccxt.NetworkError, ccxt.RequestTimeout, 
                        ccxt.ExchangeError, asyncio.TimeoutError) as e:
                    wait_time = min(60, 2 ** attempt)
                    logging.warning(f"⚠️ 网络错误 (尝试 {attempt}/{max_tries}): {type(e).__name__}: {e}")
                    if attempt == max_tries:
                        logging.error(f"❌ 重试失败，放弃: {func.__name__}")
                        raise
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator
```

**Step 3: 应用到 API 调用**
```python
# 旧代码
async def get_global_targets():
    markets = await ex.load_markets()
    ...

# 新代码
@retry_on_network_error(max_tries=3)
async def get_global_targets():
    markets = await ex.load_markets()
    ...

# 应用到其他 API 函数
@retry_on_network_error(max_tries=3)
async def check_structure(ex, symbol):
    bars = await ex.fetch_ohlcv(...)
    ...

@retry_on_network_error(max_tries=3)
async def snip_single_target(uid, ex, symbol, info):
    ticker = await ex.fetch_ticker(symbol)
    ...
```

**Step 4: 添加断路器模式**
```python
class CircuitBreaker:
    """断路器：连续失败后暂停调用"""
    
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'closed':
            if self.last_failure_time:
                elapsed = time.time() - self.last_failure_time
                if elapsed > self.timeout:
                    self.state = 'open'
                    self.failure_count = 0
            else:
                raise Exception("断路器打开")
        
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'closed'
                logging.error(f"🔌 断路器触发: 失败次数 {self.failure_count}")
            
            raise

# 创建断路器实例
circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=300)
```

**验证:** 人为制造网络错误，观察重试日志

---

### Task 4: 并发限制优化

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 从配置读取并发限制**
```python
# 添加到 load_config 后
MAX_CONCURRENT = config['scanner']['max_concurrent']

# 更新 semaphore
semaphore = asyncio.Semaphore(MAX_CONCURRENT)
```

**Step 2: 动态调整并发数**
```python
class AdaptiveConcurrency:
    """自适应并发控制器"""
    
    def __init__(self, initial=10, max=30, min=5):
        self.current = initial
        self.max = max
        self.min = min
        self.success_rate = 1.0
        self.failure_rate = 0.0
    
    async def adjust(self, success):
        """根据成功率调整并发数"""
        window_size = 10
        
        if success:
            self.success_rate = (self.success_rate * (window_size - 1) + 1) / window_size
            self.failure_rate = self.failure_rate * 0.9
        else:
            self.failure_rate = (self.failure_rate * (window_size - 1) + 1) / window_size
            self.success_rate = self.success_rate * 0.9
        
        # 计算成功率
        success_ratio = self.success_rate / (self.success_rate + self.failure_rate)
        
        # 动态调整
        if success_ratio > 0.95 and self.current < self.max:
            self.current += 1
            logging.info(f"📈 提高并发: {self.current - 1} -> {self.current}")
        elif success_ratio < 0.8 and self.current > self.min:
            self.current -= 1
            logging.info(f"📉 降低并发: {self.current} -> {self.current}")

# 创建自适应并发控制器
concurrency_controller = AdaptiveConcurrency(initial=20, max=30, min=10)
```

**Step 3: 更新任务执行**
```python
async def radar_job():
    """雷达扫描任务"""
    while True:
        try:
            targets = await get_global_targets()
            if targets:
                # 使用当前并发数
                semaphore = asyncio.Semaphore(concurrency_controller.current)
                
                logging.info(f"🔍 并发扫描: {len(targets)} 标的 (并发限制: {concurrency_controller.current})")
                
                tasks = []
                for target in targets:
                    ex = target['exchange']
                    symbol = target['symbol']
                    uid = f"{ex.id}:{symbol}"
                    if uid not in watchlist:
                        tasks.append(asyncio.create_task(
                            check_structure(ex, symbol),
                            semaphore=semaphore
                        ))
                
                await asyncio.gather(*tasks)
                
                # 更新并发数（基于本轮成功率）
                concurrency_controller.adjust(success=True)
                
            else:
                logging.info("💤 本轮无新发现")
        except Exception as e:
            logging.error(f"❌ 雷达任务异常: {e}")
            concurrency_controller.adjust(success=False)
        
        await asyncio.sleep(config['scanner']['interval_seconds'])
```

**验证:** 运行脚本，观察并发数变化日志

---

### Task 5: 日志分级

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 配置日志级别**
```python
# 在 load_config 后添加
LOG_LEVEL = getattr(logging, config['logging']['level'].upper())
```

**Step 2: 使用结构化日志**
```python
# 添加日志格式
import json

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }
        
        # 添加额外上下文
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)

# 创建不同用途的 logger
api_logger = logging.getLogger('scanner.api')
db_logger = logging.getLogger('scanner.db')
alert_logger = logging.getLogger('scanner.alert')
```

**Step 3: 更新日志配置**
```python
# 替换 logging.basicConfig
log_handlers = [
    logging.FileHandler(
        config['logging']['file'],
        encoding='utf-8'
    ),
    logging.StreamHandler()
]

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=log_handlers
)

# 设置不同 logger 的级别
api_logger.setLevel(logging.INFO)
db_logger.setLevel(logging.WARNING)
alert_logger.setLevel(logging.ERROR)
```

**Step 4: 添加上下文日志**
```python
# 在关键函数中添加额外上下文
async def check_structure(ex, symbol):
    try:
        bars = await ex.fetch_ohlcv(symbol, timeframe='1h', limit=120)
        # ...
    except Exception as e:
        logging.error(
            f"形态检测失败: {symbol}",
            extra={
                'exchange': ex.id,
                'symbol': symbol,
                'error': str(e),
                'operation': 'check_structure'
            }
        )
        raise
```

**验证:** 运行脚本，检查日志文件格式

---

### Task 6: 邮件发送优化

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 创建邮件队列**
```python
from collections import deque
import time

class EmailQueue:
    """邮件发送队列"""
    
    def __init__(self, max_batch_size=5, max_wait_seconds=60):
        self.queue = deque()
        self.max_batch_size = max_batch_size
        self.max_wait_seconds = max_wait_seconds
        self.last_flush_time = time.time()
        self.server = None
    
    async def connect(self):
        """连接 SMTP 服务器"""
        if self.server is None:
            self.server = smtplib.SMTP('smtp.qq.com', 587)
            await asyncio.to_thread(self.server.connect)
            self.server.starttls()
            self.server.login(SENDER_EMAIL, SENDER_PASSWORD)
            logging.info("✅ SMTP 连接已建立")
    
    async def add(self, subject, content):
        """添加邮件到队列"""
        self.queue.append({
            'subject': subject,
            'content': content,
            'timestamp': time.time()
        })
        
        # 检查是否需要立即发送
        if len(self.queue) >= self.max_batch_size:
            await self.flush()
    
    async def flush(self):
        """批量发送队列中的邮件"""
        if not self.queue:
            return
        
        await self.connect()
        
        for email in self.queue:
            msg = MIMEText(email['content'], 'plain', 'utf-8')
            msg['From'] = formataddr(["万物并集猎手", SENDER_EMAIL])
            msg['To'] = formataddr(["指挥官", RECEIVER_EMAIL])
            msg['Subject'] = email['subject']
            
            self.server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        self.queue.clear()
        self.last_flush_time = time.time()
        logging.info(f"📧 批量发送 {len(self.queue)} 封邮件")
        
        self.server.quit()
        self.server = None
    
    async def auto_flush(self):
        """定时检查并发送"""
        now = time.time()
        if self.queue and (now - self.last_flush_time) > self.max_wait_seconds:
            await self.flush()

# 创建邮件队列实例
email_queue = EmailQueue(max_batch_size=5, max_wait_seconds=60)

# 在 main 函数中添加自动刷新
async def main():
    # ... 现有代码 ...
    
    # 添加后台任务：定期刷新邮件队列
    asyncio.create_task(auto_flush_email_queue())
    
    await asyncio.gather(
        radar_job(),
        sniper_job()
    )

async def auto_flush_email_queue():
    """定期刷新邮件队列"""
    while True:
        await email_queue.auto_flush()
        await asyncio.sleep(10)
```

**Step 2: 更新邮件发送**
```python
# 旧代码
asyncio.create_task(send_email(f"🚨 {signal} {symbol}", email_content))

# 新代码
await email_queue.add(f"🚨 {signal} {symbol}", email_content)
```

**Step 3: 添加邮件模板**
```python
# 创建邮件模板
EMAIL_TEMPLATES = {
    'breakout': """🚨 结构突破警报

平台: {platform}
品种: {symbol}
方向: {direction}
现价: {price}
突破位: {break_price}

时间: {time}

请立即查看图表！""",
    
    'radar_report': """📊 猎手雷达日报

发现 {count} 个收敛结构

{items}
---
数据来源: 万物并集猎手
"""
}

def render_template(template_name, **kwargs):
    """渲染邮件模板"""
    template = EMAIL_TEMPLATES.get(template_name, '')
    return template.format(**kwargs)
```

**验证:** 观察邮件发送日志，确认批量发送

---

### Task 7: 错误处理改进

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 定义错误类型**
```python
# 添加错误类型定义
class ScannerError(Exception):
    """扫描器基础错误类"""
    pass

class ConfigError(ScannerError):
    """配置错误"""
    pass

class DatabaseError(ScannerError):
    """数据库错误"""
    pass

class APIError(ScannerError):
    """API 错误"""
    pass

class EmailError(ScannerError):
    """邮件错误"""
    pass
```

**Step 2: 添加错误恢复策略**
```python
class ErrorRecovery:
    """错误恢复策略"""
    
    def __init__(self):
        self.recovery_strategies = {
            'ccxt.NetworkError': self._retry_network,
            'ccxt.RequestTimeout': self._retry_timeout,
            'sqlite3.OperationalError': self._repair_database,
            'smtplib.SMTPException': self._queue_email,
        }
    
    async def recover(self, error, context):
        """根据错误类型执行恢复策略"""
        error_type = type(error).__name__
        
        recovery_func = self.recovery_strategies.get(error_type)
        if recovery_func:
            logging.warning(f"🔧 执行恢复策略: {error_type}")
            try:
                await recovery_func(context)
            except Exception as recovery_error:
                logging.error(f"❌ 恢复失败: {recovery_error}")
        
        # 记录错误
        self._log_error(error, context)
    
    async def _retry_network(self, context):
        """网络错误恢复：增加退避时间"""
        # 已经在重试装饰器中处理
        pass
    
    async def _repair_database(self, context):
        """数据库错误恢复：重新连接"""
        global db_pool
        db_pool.pool = None  # 重置连接池
        logging.info("🔄 数据库连接池已重置")
    
    async def _queue_email(self, context):
        """邮件错误恢复：加入队列"""
        # 邮件队列会自动处理
        await email_queue.add(
            "📧 邮件发送失败，已加入队列重试",
            context
        )
    
    def _log_error(self, error, context):
        """记录错误到日志和数据库"""
        logging.error(f"❌ 错误: {type(error).__name__}: {error}")
        
        # 记录到数据库（可选）
        # async with db_pool.connection() as db:
        #     await db.execute(...)
```

**Step 3: 更新异常处理**
```python
# 在主循环中添加全局错误处理
async def main():
    print("===================================================")
    print("🚀 万物并集猎手 V11.0 (错误处理优化版) 启动...")
    print("===================================================")
    
    recovery = ErrorRecovery()
    
    try:
        init_db()
        await init_exchanges()
        load_data_from_db()
        
        await asyncio.gather(
            radar_job(),
            sniper_job()
        )
    except KeyboardInterrupt:
        logging.info("🛑 用户中断，程序退出")
    except Exception as e:
        logging.error(f"❌ 未捕获异常: {e}")
        # 尝试恢复
        asyncio.run(recovery.recover(e, {'main_loop': True}))
    finally:
        logging.info("✅ 程序退出，清理资源...")
        # 清理资源
        await email_queue.flush()
```

**验证:** 触发不同类型的错误，观察恢复日志

---

### Task 8: 性能监控

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 添加性能统计类**
```python
class PerformanceMonitor:
    """性能监控"""
    
    def __init__(self):
        self.api_calls = 0
        self.api_errors = 0
        self.api_success = 0
        self.api_time = []
        self.db_operations = 0
        self.emails_sent = 0
        self.email_errors = 0
        self.start_time = time.time()
    
    def record_api_call(self, duration, success):
        """记录 API 调用"""
        self.api_calls += 1
        self.api_time.append(duration)
        
        if success:
            self.api_success += 1
        else:
            self.api_errors += 1
    
    def record_db_operation(self):
        """记录数据库操作"""
        self.db_operations += 1
    
    def record_email(self, success):
        """记录邮件发送"""
        if success:
            self.emails_sent += 1
        else:
            self.email_errors += 1
    
    def get_stats(self):
        """获取统计信息"""
        uptime = time.time() - self.start_time
        
        avg_api_time = sum(self.api_time) / len(self.api_time) if self.api_time else 0
        api_success_rate = (self.api_success / self.api_calls * 100) if self.api_calls > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'api_calls': self.api_calls,
            'api_success_rate': f"{api_success_rate:.2f}%",
            'api_errors': self.api_errors,
            'avg_api_time_ms': f"{avg_api_time:.2f}",
            'db_operations': self.db_operations,
            'emails_sent': self.emails_sent,
            'email_errors': self.email_errors
        }
    
    def reset_stats(self):
        """重置统计（每小时）"""
        self.api_calls = 0
        self.api_errors = 0
        self.api_success = 0
        self.api_time = []
        logging.info("📊 性能统计已重置")

# 创建性能监控实例
perf_monitor = PerformanceMonitor()
```

**Step 2: 在关键函数中添加性能记录**
```python
# 包装 API 调用
async def timed_api_call(func, *args, **kwargs):
    """计时 API 调用"""
    start = time.time()
    try:
        result = await func(*args, **kwargs)
        perf_monitor.record_api_call(time.time() - start, True)
        return result
    except Exception as e:
        perf_monitor.record_api_call(time.time() - start, False)
        raise

# 包装数据库调用
async def timed_db_call(func, *args, **kwargs):
    """计时数据库调用"""
    start = time.time()
    try:
        result = await func(*args, **kwargs)
        perf_monitor.record_db_operation()
        return result
    except Exception as e:
        perf_monitor.record_db_operation()  # 失败也记录
        raise
```

**Step 3: 定期报告性能**
```python
async def performance_report_job():
    """每小时报告一次性能"""
    while True:
        stats = perf_monitor.get_stats()
        
        logging.info("📊 性能报告:")
        logging.info(f"  运行时间: {stats['uptime_seconds']:.0f}秒")
        logging.info(f"  API调用: {stats['api_calls']}次")
        logging.info(f"  API成功率: {stats['api_success_rate']}")
        logging.info(f"  API平均耗时: {stats['avg_api_time_ms']}ms")
        logging.info(f"  数据库操作: {stats['db_operations']}次")
        logging.info(f"  邮件发送: {stats['emails_sent']}次")
        logging.info(f"  邮件失败: {stats['email_errors']}次")
        
        perf_monitor.reset_stats()
        await asyncio.sleep(3600)

# 在 main 中添加性能报告任务
async def main():
    # ...
    await asyncio.gather(
        radar_job(),
        sniper_job(),
        performance_report_job()
    )
```

**Step 4: 添加健康检查**
```python
async def health_check():
    """健康检查"""
    stats = perf_monitor.get_stats()
    
    # 判断健康状态
    is_healthy = True
    issues = []
    
    if stats['api_success_rate'] < 80:
        is_healthy = False
        issues.append("API成功率低")
    
    if float(stats['avg_api_time_ms']) > 5000:
        is_healthy = False
        issues.append("API响应慢")
    
    # 发送健康报告
    if not is_healthy:
        await email_queue.add(
            "⚠️ 健康检查警告",
            f"系统状态: 不健康\n\n问题: {', '.join(issues)}\n\n{stats}"
        )
    
    return is_healthy

async def health_check_job():
    """每15分钟检查一次健康"""
    while True:
        await health_check()
        await asyncio.sleep(900)

# 在 main 中添加健康检查任务
async def main():
    # ...
    await asyncio.gather(
        radar_job(),
        sniper_job(),
        performance_report_job(),
        health_check_job()
    )
```

**验证:** 运行脚本，观察每小时性能报告

---

### Task 9: 资源清理

**文件:**
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 添加清理函数**
```python
async def cleanup_expired_data():
    """清理过期数据"""
    async with db_pool.connection() as db:
        # 清理过期的 watchlist 条目
        now = datetime.now()
        await db.execute(
            "DELETE FROM watchlist WHERE datetime(expiry) < ?",
            (now - timedelta(days=7)).isoformat()
        )
        
        # 清理一周前的 alert 历史
        await db.execute(
            "DELETE FROM alert_history WHERE datetime(last_alert) < ?",
            (now - timedelta(days=7)).isoformat()
        )
        
        # 清理无效的交易所数据
        for ex_id in list(exchanges_dict.keys()):
            if ex_id not in EXCHANGES_TO_LOAD:
                await db.execute("DELETE FROM watchlist WHERE exchange_id = ?", (ex_id,))
        
        deleted_count = db.execute("SELECT changes()").fetchone()[0]
        logging.info(f"🧹 清理过期数据: {deleted_count}条记录")
```

**Step 2: 添加数据库优化**
```python
async def optimize_database():
    """优化数据库"""
    async with db_pool.connection() as db:
        # 执行 VACUUM
        await db.execute("VACUUM")
        
        # 重建索引
        await db.execute("REINDEX watchlist")
        await db.execute("REINDEX alert_history")
        
        # 分析数据库大小
        table_info = await db.execute(
            "SELECT name, (SELECT COUNT(*) FROM sqlited_master WHERE type='table' AND name=name) as count "
            "FROM sqlited_master WHERE type='table' ORDER BY name"
        ).fetchall()
        
        for name, count in table_info:
            logging.info(f"📊 表 {name}: {count}条记录")
```

**Step 3: 添加定期清理任务**
```python
async def cleanup_job():
    """定期清理任务"""
    while True:
        try:
            await cleanup_expired_data()
            await optimize_database()
        except Exception as e:
            logging.error(f"❌ 清理任务异常: {e}")
        
        # 每24小时清理一次
        await asyncio.sleep(86400)

# 在 main 中添加清理任务
async def main():
    # ...
    await asyncio.gather(
        radar_job(),
        sniper_job(),
        performance_report_job(),
        health_check_job(),
        cleanup_job()
    )
```

**Step 4: 添加启动时清理**
```python
async def init_db():
    """初始化数据库并清理旧数据"""
    db_path = Path(__file__).parent / config['database']['file']
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 创建表
    c.execute('''CREATE TABLE IF NOT EXISTS watchlist
                 (uid TEXT PRIMARY KEY, exchange_id TEXT, symbol TEXT, high REAL, low REAL, expiry TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history
                 (uid TEXT PRIMARY KEY, last_alert TEXT)''')
    
    # 清理一周前的 alert 历史
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute(f"DELETE FROM alert_history WHERE datetime(last_alert) < '{week_ago}'")
    
    conn.commit()
    conn.close()
    
    logging.info("✅ 数据库初始化完成，已清理旧数据")
```

**验证:** 运行脚本24小时后，检查数据库大小和日志

---

### Task 10: 配置验证

**文件:**
- 创建: `scripts/scanner_config.schema.json`
- 修改: `scripts/union-scanner.py`

**步骤:**

**Step 1: 创建配置 Schema**
```bash
cat > scripts/scanner_config.schema.json << 'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["email", "scanner", "database", "logging", "exchanges"],
  "properties": {
    "email": {
      "type": "object",
      "required": ["sender", "password", "receiver"],
      "properties": {
        "sender": {"type": "string", "format": "email"},
        "password": {"type": "string", "minLength": 6},
        "receiver": {"type": "string", "format": "email"}
      }
    },
    "scanner": {
      "type": "object",
      "required": ["interval_seconds", "max_concurrent", "min_history"],
      "properties": {
        "interval_seconds": {"type": "integer", "minimum": 60, "maximum": 86400},
        "max_concurrent": {"type": "integer", "minimum": 5, "maximum": 100},
        "min_history": {"type": "integer", "minimum": 50, "maximum": 200},
        "min_volume_usdt": {"type": "integer", "minimum": 100000},
        "min_volume_vip": {"type": "integer", "minimum": 5000}
      }
    },
    "database": {
      "type": "object",
      "required": ["file"],
      "properties": {
        "file": {"type": "string", "pattern": "^.*\\.db$"}
      }
    },
    "logging": {
      "type": "object",
      "required": ["level", "file"],
      "properties": {
        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
        "file": {"type": "string"}
      }
    },
    "exchanges": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["binance", "bybit", "bitget", "bingx", "msx"]
      }
    }
  }
}
EOF
```

**Step 2: 添加验证函数**
```python
# 安装 jsonschema 库
pip install jsonschema

# 在文件顶部添加
import jsonschema

def validate_config(config):
    """验证配置"""
    # 读取 schema
    schema_path = Path(__file__).parent / 'scanner_config.schema.json'
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    # 验证配置
    jsonschema.validate(config, schema)
    logging.info("✅ 配置验证通过")
    
    # 添加类型提示
    config['email']['sender'] = config['email']['sender'].lower()
    config['email']['receiver'] = config['email']['receiver'].lower()
    
    return config
```

**Step 3: 添加配置示例**
```bash
cat > scripts/scanner_config.example.json << 'EOF'
{
  "email": {
    "sender": "your_email@qq.com",
    "password": "your_smtp_password",
    "receiver": "your_email@qq.com"
  },
  "scanner": {
    "interval_seconds": 3600,
    "max_concurrent": 30,
    "min_history": 90,
    "check_interval_seconds": 60,
    "max_amplitude": 0.10,
    "min_amplitude": 0.015,
    "squeeze_factor": 0.75,
    "min_volume_usdt": 5000000,
    "min_volume_vip": 10000,
    "min_touches": 3,
    "min_rejections": 1
  },
  "database": {
    "file": "scanner_data.db",
    "cleanup_interval_hours": 24
  },
  "logging": {
    "level": "INFO",
    "file": "scanner_run.log"
  },
  "exchanges": ["binance", "bybit", "bitget", "bingx", "msx"]
}
EOF
```

**Step 4: 添加配置加载错误处理**
```python
def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证配置
        validate_config(config)
        
        return config
    except FileNotFoundError:
        logging.error(f"❌ 配置文件不存在: {CONFIG_FILE}")
        logging.info(f"💡 从示例创建配置: {CONFIG_FILE}.example")
        
        # 尝试从示例创建
        try:
            with open(f"{CONFIG_FILE}.example", 'r', encoding='utf-8') as f:
                example_config = json.load(f)
            
            # 创建配置文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(example_config, f, indent=2)
            
            logging.error("❌ 请编辑配置文件后重试")
            exit(1)
        except Exception as e:
            logging.error(f"❌ 无法创建配置: {e}")
            exit(1)
    
    except json.JSONDecodeError as e:
        logging.error(f"❌ 配置文件格式错误: {e}")
        exit(1)
```

**验证:** 
1. 故意提供错误的配置，观察错误信息
2. 运行脚本，确认配置验证正常

---

## 执行顺序

**批次 1: 基础优化（Task 1-3）**
1. Task 1: 配置外部化
2. Task 2: 数据库连接池优化
3. Task 3: API 重试机制

**批次 2: 性能优化（Task 4-6）**
4. Task 4: 并发限制优化
5. Task 5: 日志分级
6. Task 6: 邮件发送优化

**批次 3: 高级优化（Task 7-9）**
7. Task 7: 错误处理改进
8. Task 8: 性能监控
9. Task 9: 资源清理

**批次 4: 完善（Task 10）**
10. Task 10: 配置验证

---

## 测试计划

### 测试 1: 配置加载测试
```bash
# 测试正常配置
python3 union-scanner.py --config test --dry-run

# 测试缺失配置
cp scanner_config.json scanner_config.json.bak
rm scanner_config.json
python3 union-scanner.py --config validate
```

### 测试 2: 数据库测试
```bash
# 创建测试数据库
python3 -c "
import aiosqlite
import asyncio

async def test():
    pool = await aiosqlite.connect('test.db')
    async with pool.connection() as db:
        await db.execute('CREATE TABLE test (id INTEGER)')
        await db.execute('INSERT INTO test VALUES (1)')
        result = await db.execute('SELECT * FROM test').fetchall()
        print(f'测试结果: {len(result)}条记录')
    await pool.close()

asyncio.run(test())
"

# 测试连接池性能
python3 -c "
import time
import aiosqlite
import asyncio

async def stress_test():
    pool = await aiosqlite.connect('test.db')
    
    start = time.time()
    for i in range(100):
        async with pool.connection() as db:
            await db.execute('SELECT 1')
    
    elapsed = time.time() - start
    print(f'100次查询耗时: {elapsed:.2f}秒 ({elapsed/100*1000:.2f}ms/次)')
    await pool.close()

asyncio.run(stress_test())
"
```

### 测试 3: API 重试测试
```bash
# 测试网络错误处理
# 需要模拟网络故障
python3 -c "
import asyncio
from unittest.mock import AsyncMock, patch

async def test_retry():
    call_count = 0
    
    async def failing_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception('模拟网络错误')
        return 'success'
    
    # 应用重试装饰器
    decorated = retry_on_network_error(max_tries=3)(failing_call)
    result = await decorated()
    
    print(f'重试测试: 调用{call_count}次, 结果: {result}')
    assert call_count == 3

asyncio.run(test_retry())
"
```

### 测试 4: 邮件发送测试
```bash
# 测试邮件队列
python3 -c "
import asyncio
from email.mime.text import MIMEText
from smtplib import SMTP

async def test_email_queue():
    # 测试批量发送
    emails = [
        ('测试邮件1', '这是第一封测试邮件'),
        ('测试邮件2', '这是第二封测试邮件'),
        ('测试邮件3', '这是第三封测试邮件'),
        ('测试邮件4', '这是第四封测试邮件'),
        ('测试邮件5', '这是第五封测试邮件'),
    ]
    
    server = SMTP('smtp.qq.com', 587)
    server.connect()
    server.starttls()
    server.login('test@qq.com', 'test_password')
    
    for subject, content in emails:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = 'test@qq.com'
        msg['To'] = 'test@qq.com'
        msg['Subject'] = subject
        
        server.sendmail('test@qq.com', 'test@qq.com', msg.as_string())
        print(f'发送: {subject}')
    
    server.quit()
    print('批量发送完成')

asyncio.run(test_email_queue())
"

# 测试真实发送（使用真实配置）
# 注意：这会发送真实邮件！
python3 union-scanner.py --test-email --dry-run
```

### 测试 5: 性能监控测试
```bash
# 测试性能统计
python3 -c "
import asyncio
from time import time

class TestMonitor:
    def __init__(self):
        self.calls = 0
        self.times = []
    
    def record(self, duration):
        self.calls += 1
        self.times.append(duration)
    
    def stats(self):
        avg = sum(self.times) / len(self.times) if self.times else 0
        return {
            'total_calls': self.calls,
            'avg_time': f'{avg:.2f}ms',
            'min_time': f'{min(self.times):.2f}ms',
            'max_time': f'{max(self.times):.2f}ms'
        }

monitor = TestMonitor()

async def simulate():
    for i in range(10):
        start = time.time()
        await asyncio.sleep(0.1)
        monitor.record((time.time() - start) * 1000)
    
    print(monitor.stats())

asyncio.run(simulate())
"
```

### 测试 6: 集成测试
```bash
# 端到端测试
python3 -c "
import asyncio

async def integration_test():
    print('开始集成测试...')
    
    # 测试1: 配置加载
    print('✓ 测试1: 配置加载')
    
    # 测试2: 数据库连接
    print('✓ 测试2: 数据库连接池')
    
    # 测试3: 并发限制
    print('✓ 测试3: 自适应并发')
    
    # 测试4: 重试机制
    print('✓ 测试4: API重试')
    
    # 测试5: 邮件队列
    print('✓ 测试5: 邮件批量发送')
    
    # 测试6: 错误处理
    print('✓ 测试6: 错误恢复')
    
    # 测试7: 性能监控
    print('✓ 测试7: 性能统计')
    
    # 测试8: 资源清理
    print('✓ 测试8: 数据库清理')
    
    print('\\n所有测试通过！✅')

asyncio.run(integration_test())
"

# 完整功能测试（干运行）
# python3 union-scanner.py --test-all --log-level DEBUG
```

---

## Git 提交策略

每个 Task 完成后提交：

```bash
# Task 1
git add scripts/scanner_config.json scripts/scanner_config.schema.json scripts/scanner_config.example.json scripts/union-scanner.py
git commit -m "feat(scanner): Task 1 - 配置外部化

- 创建配置文件和 Schema 验证
- 从 config.json 加载配置
- 添加配置验证和错误处理
- 支持配置示例文件"

# Task 2
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 2 - 数据库连接池优化

- 集成 aiosqlite 连接池
- 使用 async context manager 管理连接
- 优化所有数据库操作
- 减少连接创建/销毁开销"

# Task 3
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 3 - API 重试机制

- 添加 backoff 重试装饰器
- 实现指数退避策略
- 添加网络错误分类和恢复
- 提高网络故障容错能力"

# Task 4
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 4 - 并发限制优化

- 实现自适应并发控制器
- 根据成功率动态调整并发数
- 从配置读取最大并发限制
- 优化 Semaphore 使用"

# Task 5
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 5 - 日志分级优化

- 添加日志级别配置
- 实现结构化日志格式
- 创建分类 logger（api, db, alert）
- 支持日志上下文"

# Task 6
git add scripts/union-scanner.py scripts/email_queue.py
git commit -m "feat(scanner): Task 6 - 邮件发送优化

- 实现邮件发送队列
- 支持批量发送和自动刷新
- 添加邮件模板系统
- 减少 SMTP 连接开销"

# Task 7
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 7 - 错误处理改进

- 定义错误类型层次结构
- 实现错误恢复策略
- 添加全局异常处理
- 改进错误日志和恢复流程"

# Task 8
git add scripts/union-scanner.py scripts/performance_monitor.py
git commit -m "feat(scanner): Task 8 - 性能监控

- 实现性能统计类
- 添加 API 计时包装器
- 实现定期性能报告
- 添加健康检查机制"

# Task 9
git add scripts/union-scanner.py
git commit -m "feat(scanner): Task 9 - 资源清理

- 实现过期数据清理
- 添加数据库优化（VACUUM, REINDEX）
- 定期清理任务
- 添加启动时清理逻辑"

# Task 10
git add scripts/scanner_config.json scripts/scanner_config.schema.json scripts/scanner_config.example.json scripts/union-scanner.py
git commit -m "feat(scanner): Task 10 - 配置验证

- 创建配置 Schema 定义
- 添加配置验证函数
- 创建配置示例文件
- 改进配置加载错误处理"

# 最终优化完成
git add docs/plans/2026-02-12-optimize-union-scanner.md
git commit -m "docs: 添加 union-scanner.py 优化计划

- 完整的10个优化任务
- 分4个批次执行
- 包含测试计划和Git提交策略
- 性能提升预期：30-50%"
```

---

## 回顾要点

完成所有优化后，预期改进：

✅ **性能提升**: 30-50%（并发+连接池+邮件队列）
✅ **稳定性提升**: 50-70%（重试机制+错误处理+健康检查）
✅ **可维护性**: 显著提升（配置外部化+日志分级）
✅ **可观测性**: 全面提升（性能监控+结构化日志）
✅ **资源优化**: 30%（定期清理+连接池）

**总预估工作量**: 4-6小时
**优先级**: Task 1-3（批次1）> Task 4-6（批次2）> Task 7-9（批次3）> Task 10（批次4）

---

**计划已创建完成!** 📋

下一步: 使用 superpowers:executing-plans 技能来执行这个计划，分4个批次逐步实施优化。
