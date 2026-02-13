#!/usr/bin/env python3
# Bitget PowerUSDT 15分钟K线实体收集突破监控脚本

import ccxt.async_support as ccxt
import pandas as pd
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timedelta

# ================= ⚙️ 用户配置 =================
SENDER_EMAIL = '371398370@qq.com'
SENDER_PASSWORD = 'hjqibancxrerbifb'
RECEIVER_EMAIL = '371398370@qq.com'

# 交易所配置
EXCHANGE = ccxt.bitget
SYMBOL = 'POWERUSDT'
TIMEFRAME = '15m'  # 15分钟K线
LOOKBACK_CANDLES = 96  # 96根15分钟 = 24小时数据
BREAKOUT_THRESHOLD = 0.42  # 实体收集突破阈值（42%）
VOLUME_SPIKE_MULTIPLIER = 2.0  # 成交量突增倍数（2倍以上）
MIN_VOLUME_THRESHOLD = 500000  # 最小成交量门槛

# API配置
API_TIMEOUT = 30000  # 30秒超时
MAX_CONCURRENT = 10  # 最大并发请求

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

async def fetch_klines(timeframe, limit):
    """获取K线数据"""
    try:
        bars = await EXCHANGE.fetch_ohlcv(SYMBOL, timeframe, limit=limit)
        if not bars:
            return None
        
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception as e:
        logging.error(f"❌ 获取K线失败 {SYMBOL}: {e}")
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
    # 标准：多次触碰相近价位，价格范围<10%
    price_levels = {}
    
    # 按价格分组
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

async def monitor_powerusdt():
    """主监控循环"""
    logging.info("🚀 Bitget PowerUSDT 15分钟K线实体收集突破监控启动")
    logging.info(f"📊 参数: 突破阈值={BREAKOUT_THRESHOLD*100}%, 成交量倍数={VOLUME_SPIKE_MULTIPLIER}x, 回溯={LOOKBACK_CANDLES}根")
    
    # 初始化交易所
    exchange = EXCHANGE({
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'},
        'timeout': API_TIMEOUT
    })
    
    # 发送记录（防止重复报警）
    alert_cache = {}
    COOLDOWN_SECONDS = 3600  # 同一突破1小时冷却
    
    retry_count = 0
    MAX_RETRIES = 3
    
    while True:
        try:
            # 获取K线数据（多取10根用于分析）
            df = await fetch_klines(TIMEFRAME, LOOKBACK_CANDLES + 10)
            
            if df is None:
                logging.warning("⚠️ 获取K线失败，等待重试...")
                await asyncio.sleep(60)
                continue
            
            # 获取最新价格
            try:
                ticker = await exchange.fetch_ticker(SYMBOL)
                current_price = ticker['last']
            except Exception as e:
                logging.error(f"❌ 获取价格失败: {e}")
                await asyncio.sleep(10)
                continue
            
            # 分析实体收集突破
            signal = analyze_accumulation(df, current_price)
            
            if signal:
                # 检查冷却时间，防止同一突破重复发邮件
                last_time = alert_cache.get('accumulation_breakout')
                if last_time and datetime.now() - last_time < timedelta(seconds=COOLDOWN_SECONDS):
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
                <p><b>实体收集结构分析:</b></p>
                <p>1. <b>收敛时长:</b> {signal['duration_hours']:.1f} 小时 ({int(signal['duration_hours'])*15} 根15mK线)</p>
                <p>2. <b>触碰次数:</b> {signal['top_touch_count']} 次</p>
                <p>3. <b>区间幅度:</b> {round((signal['high'] - signal['low']) / signal['low'] * 100, 2)}%</p>
                <p>4. <b>区间高低:</b> ${signal['low']} - ${signal['high']}</p>
                <hr>
                <p><b>成交量分析:</b></p>
                <p>• <b>当前成交量:</b> {signal['volume_spike']:,.0f}</p>
                <p>• <b>平均成交量:</b> {signal['avg_volume']:,.0f}</p>
                <p>• <b>成交量倍数:</b> {signal['volume_spike'] / signal['avg_volume']:.2f}x</p>
                <hr>
                <p><b>战术建议:</b></p>
                <p>这是一次经过充分蓄势({int(signal['duration_hours'])*15}根15mK线)的实体收集突破。</p>
                <p>当前价格刚刚探头，请立即查看图表确认成交量配合情况。</p>
                <p>• <b>做多位:</b> 价格突破实体收集区间高点，并伴随2倍以上成交量</p>
                <p>• <b>止损建议:</b> 实体收集区间中轴或最近的收敛K线低点</p>
                <p>• <b>目标位:</b> ${signal['high']}</p>
                <hr>
                <p><b>⚠️ 风险提示:</b></p>
                <p>• 注意假突破风险（未获成交量支撑）</p>
                <p>• 建议分批建仓，控制仓位</p>
                """
                
                # 发送邮件
                if send_email(f"【实体收集突破】{SYMBOL} 突破{signal['duration_hours']:.1f}h箱体!", email_content, is_html=True):
                    alert_cache['accumulation_breakout'] = datetime.now()
                    logging.info("✅ 报警已发送")
            
            # 记录状态
            logging.info(f"📊 价格: ${current_price} | 信号: {'实体收集突破' if signal else '无信号'}")
            
            # 重置重试计数
            retry_count = 0
            
            # 等待下一个周期
            await asyncio.sleep(60)  # 每1分钟检查一次
            
        except KeyboardInterrupt:
            logging.info("🛑 用户中断，程序退出")
            break
        except Exception as e:
            retry_count += 1
            logging.error(f"❌ 主循环异常: {e}")
            
            if retry_count < MAX_RETRIES:
                logging.warning(f"🔄 重试中 ({retry_count}/{MAX_RETRIES})...")
                await asyncio.sleep(60)
            else:
                logging.error("❌ 达到最大重试次数，等待人工干预")
                await asyncio.sleep(300)  # 等待5分钟

if __name__ == "__main__":
    print("===================================================")
    print("🚀 Bitget PowerUSDT 15分钟K线实体收集突破监控启动")
    print("===================================================")
    
    try:
        asyncio.run(monitor_powerusdt())
    except KeyboardInterrupt:
        pass
