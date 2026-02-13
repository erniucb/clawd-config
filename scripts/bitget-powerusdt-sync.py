#!/usr/bin/env python3
# Bitget PowerUSDT 15分钟K线实体收集突破监控脚本（同步版本）

import ccxt
import pandas as pd
import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta
import time

# ================= ⚙️ 用户配置 =================
SENDER_EMAIL = '371398370@qq.com'
SENDER_PASSWORD = 'hjqibancxrerbifb'
RECEIVER_EMAIL = '371398370@qq.com'

# 交易所配置
EXCHANGE_ID = 'bitget'
SYMBOL = 'POWERUSDT'
TIMEFRAME = '15m'  # 15分钟K线
LOOKBACK_CANDLES = 96  # 96根15分钟 = 24小时数据
BREAKOUT_THRESHOLD = 0.42  # 实体收集突破阈值（42%）
VOLUME_SPIKE_MULTIPLIER = 2.0  # 成交量突增倍数（2倍以上）
MIN_VOLUME_THRESHOLD = 500000  # 最小成交量门槛

# API配置
API_TIMEOUT = 30  # 30秒超时（同步版本不需要太久）
MAX_RETRIES = 3  # 最大重试次数

# ================= 📝 日志系统 =================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/root/clawd/scripts/bitget-monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================= 📧 邮件系统 =================
def send_email(subject, content, is_html=False):
    """发送邮件"""
    try:
        msg_type = 'html' if is_html else 'plain'
        msg = MIMEText(content, msg_type, 'utf-8')
        msg['From'] = formataddr(["Bitget监控器", SENDER_EMAIL])
        msg['To'] = formataddr(["交易员", RECEIVER_EMAIL])
        msg['Subject'] = subject
        
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        logging.info(f"✅ 邮件发送成功: {subject}")
        return True
    except Exception as e:
        logging.error(f"❌ 邮件发送失败: {e}")
        return False

# ================= 🔧 核心功能（同步版本）====================

def init_exchange():
    """初始化交易所（同步版本）"""
    try:
        exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {'defaultType': 'swap'},
            'timeout': API_TIMEOUT * 1000
        })
        
        # 测试连接
        markets = exchange.load_markets()
        logging.info(f"✅ Bitget 连接成功，市场数量: {len(markets)}")
        
        return exchange
    except Exception as e:
        logging.error(f"❌ Bitget 初始化失败: {e}")
        raise

def fetch_klines_with_retry(exchange, symbol, timeframe, limit):
    """带重试机制获取K线数据"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            logging.debug(f"✅ 获取K线成功 (尝试 {attempt}): {len(bars)}根")
            return bars
        except (ccxt.NetworkError, ccxt.RequestTimeout, ccxt.ExchangeError) as e:
            wait_time = min(60, 2 ** (attempt - 1))
            logging.warning(f"⚠️ 获取K线失败 (尝试 {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            
            if attempt < MAX_RETRIES:
                logging.info(f"🔄 等待 {wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                logging.error(f"❌ 获取K线失败，已达到最大重试次数: {e}")
                return None
        except Exception as e:
            logging.error(f"❌ 获取K线异常: {e}")
            return None

def analyze_accumulation(df, current_price):
    """分析实体收集突破"""
    if df is None or len(df) < LOOKBACK_CANDLES:
        return None
    
    # 取前96根K线（24小时）
    accumulation_df = df.head(LOOKBACK_CANDLES)
    
    # 计算实体收集指标
    highs = accumulation_df['high']
    lows = accumulation_df['low']
    volumes = accumulation_df['volume']
    
    # 识别实体收集区间（收敛：多次触碰相近价位，波动逐渐减小）
    price_levels = {}
    
    for idx, row in accumulation_df.iterrows():
        price = row['close']
        price_rounded = round(price, 4)
        
        if price_rounded not in price_levels:
            price_levels[price_rounded] = {
                'touch_count': 1,
                'total_volume': row['volume'],
                'first_touch': idx,
                'last_touch': idx
            }
        else:
            price_levels[price_rounded]['touch_count'] += 1
            price_levels[price_rounded]['total_volume'] += row['volume']
            price_levels[price_rounded]['last_touch'] = idx
    
    # 找出实体收集区间（至少3次触碰，价格范围<10%）
    accumulation_zones = []
    for price, data in price_levels.items():
        if data['touch_count'] >= 3:
            range_percent = (data['high'] - data['low']) / data['low'] * 100
            
            if range_percent < 10:
                accumulation_zones.append({
                    'price_level': price,
                    'touch_count': data['touch_count'],
                    'total_volume': data['total_volume'],
                    'duration_hours': (data['last_touch'] - data['first_touch']) * 15 / 3600,
                    'high': data['high'],
                    'low': data['low']
                })
    
    # 按触碰次数排序（越多越可能是强支撑/阻力）
    accumulation_zones.sort(key=lambda x: x['touch_count'], reverse=True)
    
    if not accumulation_zones:
        return None
    
    # 检查是否突破最高实体收集区间
    top_zone = accumulation_zones[0]
    breakout = current_price > top_zone['high']
    
    # 成交量检查（突破时成交量至少是平均的2倍）
    avg_volume = df['volume'].mean()
    volume_spike = current_price > top_zone['high'] and (df.iloc[-1]['volume'] > avg_volume * VOLUME_SPIKE_MULTIPLIER)
    
    # 完整的突破条件
    if breakout and volume_spike:
        return {
            'type': 'accumulation_breakout',
            'zone': top_zone,
            'current_price': current_price,
            'top_touch_count': top_zone['touch_count'],
            'duration_hours': top_zone['duration_hours'],
            'high': top_zone['high'],
            'low': top_zone['low'],
            'volume_spike': df.iloc[-1]['volume'],
            'avg_volume': avg_volume
        }
    
    return None

def monitor_powerusdt():
    """主监控循环（同步版本）"""
    logging.info("🚀 Bitget PowerUSDT 15分钟K线实体收集突破监控启动（同步版本）")
    logging.info(f"📊 参数: 突破阈值={BREAKOUT_THRESHOLD*100}%, 成交量倍数={VOLUME_SPIKE_MULTIPLIER}x, 回溯={LOOKBACK_CANDLES}根")
    
    # 初始化交易所
    exchange = init_exchange()
    
    # 发送记录（防止重复报警）
    alert_cache = {}
    COOLDOWN_SECONDS = 3600  # 同一突破1小时冷却
    
    while True:
        try:
            # 获取K线数据（多取10根用于分析）
            bars = fetch_klines_with_retry(exchange, SYMBOL, TIMEFRAME, LOOKBACK_CANDLES + 10)
            
            if bars is None:
                logging.warning("⚠️ 获取K线失败，等待重试...")
                time.sleep(60)
                continue
            
            # 转换为DataFrame
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # 获取最新价格
            current_price = df.iloc[-1]['close']
            
            # 分析实体收集突破
            signal = analyze_accumulation(df, current_price)
            
            if signal:
                # 检查冷却时间
                last_time = alert_cache.get('accumulation_breakout')
                now = datetime.now()
                
                if last_time and (now - last_time).total_seconds() < COOLDOWN_SECONDS:
                    logging.info("❄️ 冷却中，跳过重复报警")
                    continue
                
                logging.warning(f"🚀 实体收集突破: {SYMBOL} @ {current_price}")
                
                # 准备邮件内容
                email_content = f"""
                <h2>🚀 Bitget 实体收集突破警报</h2>
                <p><b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p><b>品种:</b> {SYMBOL} ({TIMEFRAME})</p>
                <p><b>当前价格:</b> ${current_price}</p>
                <hr>
                <h3>📊 实体收集结构分析</h3>
                <table border="1" cellspacing="0" cellpadding="5">
                    <tr><td><b>突破位置:</b></td><td>${signal['high']}</td></tr>
                    <tr><td><b>实体收集时长:</b></td><td>{signal['duration_hours']:.1f}小时</td></tr>
                    <tr><td><b>触碰次数:</b></td><td>{signal['top_touch_count']}次</td></tr>
                    <tr><td><b>区间幅度:</b></td><td>{(signal['high'] - signal['low']) / signal['low'] * 100:.2f}%</td></tr>
                </table>
                <hr>
                <h3>💹 成交量分析</h3>
                <table border="1" cellspacing="0" cellpadding="5">
                    <tr><td><b>当前成交量:</b></td><td>{signal['volume_spike']:,.0f}</td></tr>
                    <tr><td><b>平均成交量:</b></td><td>{signal['avg_volume']:,.0f}</td></tr>
                    <tr><td><b>成交量倍数:</b></td><td>{signal['volume_spike'] / signal['avg_volume']:.2f}x</td></tr>
                </table>
                <hr>
                <h3>🎯 战术建议</h3>
                <p>这是一次经过充分蓄势({signal['duration_hours']:.1f}小时 = {int(signal['duration_hours'])*15}根{TIMEFRAME}K线)的实体收集突破。</p>
                <ul>
                    <li><b>做多信号:</b> 价格突破实体收集区间高点，并伴随{signal['volume_spike']/signal['avg_volume']:.1f}倍成交量</li>
                    <li><b>止损建议:</b> 实体收集区间中轴或最近的收敛K线低点</li>
                    <li><b>风险提示:</b> 注意假突破风险，建议等待K线收盘确认</li>
                    <li><b>仓位管理:</b> 建议分批建仓，控制单一仓位风险</li>
                </ul>
                <hr>
                <p style="color: #666;"><b>⚠️ 请立即查看图表确认形态！</b></p>
                """
                
                # 发送邮件
                if send_email(f"【实体收集突破】{SYMBOL} 突破{signal['duration_hours']:.1f}h箱体!", email_content, is_html=True):
                    alert_cache['accumulation_breakout'] = datetime.now()
                    logging.info("✅ 报警已发送")
            
            # 记录状态
            logging.info(f"📊 价格: ${current_price} | 信号: {'实体收集突破' if signal else '无信号'}")
            
            # 等待下一个周期
            time.sleep(60)  # 每分钟检查一次
            
        except KeyboardInterrupt:
            logging.info("🛑 用户中断，程序退出")
            break
        except Exception as e:
            logging.error(f"❌ 主循环异常: {e}")
            logging.error(f"💡 将在60秒后重试...")
            time.sleep(60)

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Bitget PowerUSDT 15分钟K线实体收集突破监控（同步版本）启动")
    print("=" * 50)
    print(f"📊 监控参数:")
    print(f"  品种: {SYMBOL}")
    print(f"  周期: {TIMEFRAME}")
    print(f"  回溯: {LOOKBACK_CANDLES}根K线")
    print(f"  突破阈值: {BREAKOUT_THRESHOLD*100}%")
    print(f"  成交量倍数: {VOLUME_SPIKE_MULTIPLIER}x")
    print(f"  邮件: {RECEIVER_EMAIL}")
    print("=" * 50)
    
    try:
        monitor_powerusdt()
    except KeyboardInterrupt:
        print("\n👋 监控已停止")
