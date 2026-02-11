# 趋势跟踪策略蒙特卡洛回测系统设计文档

**日期:** 2026-02-10
**用户:** web3Traval (爸爸)
**策略类型:** 趋势跟踪型
**K线周期:** 4小时线

---

## 一、策略规则

### 1.1 入场条件（三阶段）

**阶段1：首次突破**
- 价格在震荡区间内波动
- 某根K线收盘价突破前高
- 记录突破K线的最高价

**阶段2：回踩确认**
- 突破后价格回落（回踩）
- 回踩的最低点**不跌破突破前的震荡区间的上沿**
- 记录回踩的最低点作为初始止损位

**阶段3：再次突破**
- 价格再次上涨，并**超过阶段1记录的突破K线最高价**
- 以当前价格入场

### 1.2 前高前低识别

- 扫描最近60根4小时K线（10天数据）
- 使用局部极值算法：
  - 前高：某根K线的最高价是前后N根中最高的
  - 前低：某根K线的最低价是前后N根中最低的
- 震荡区间：前高到前低之间的价格范围

### 1.3 止盈止损规则

**初始状态：**
- 止损线 = 回踩低点
- 状态：风险中（止损线 < 入场价）

**第一次盘整：**
- 价格突破后到达新的震荡区间（连续2-3根K线横盘）
- 止损线提高到**入场价**
- 状态：保本/盈利（止损线 ≥ 入场价）

**后续盘整：**
- 价格继续突破，到达下一个震荡区间
- 止损线提高到**上一个盘整区间的下沿**
- 梯次锁定利润

**止损触发：**
- 价格跌破止损线，立即平仓

### 1.4 风险管理

**仓位计算：**
```
仓位 = (总资金 × 2%) ÷ (入场价 - 止损价)
```
- 止损距离越小，仓位越大
- 每次单笔止损最大金额：总资金的2%

**持仓限制：**
- 同时持有最多3个**风险仓位**（止损线 < 入场价）
- 已保本/盈利的仓位（止损线 ≥ 入场价）不计入持仓数量
- 全部止损上限：总资金的6%（3 × 2%）

**状态定义：**
- 🔴 风险中：止损线 < 入场价
- 🟢 保本/盈利：止损线 ≥ 入场价

---

## 二、系统架构

### 2.1 模块划分

**1. 数据生成模块（data_generator.py）**
- 基于BTC历史波动率（约2-3%日波动）生成模拟数据
- 使用几何布朗运动模型
- 加入趋势性（随机漂移）
- 每次生成约1年的4小时K线数据（约2190根）

**2. 策略执行模块（strategy_engine.py）**
- 实现三阶段入场逻辑
- 前高前低识别
- 仓位计算
- 止盈止损管理
- 持仓状态跟踪

**3. 蒙特卡洛模拟器（monte_carlo.py）**
- 运行100次独立模拟
- 收集每次模拟的交易数据
- 并行执行（可选）

**4. 统计分析模块（analytics.py）**
- 计算核心指标
- 生成分布统计
- 计算置信区间

**5. 报告生成模块（reporter.py）**
- 生成文本报告
- 生成图表（收益率分布、最大回撤分布、资金曲线）

### 2.2 数据流程

```
生成单条数据路径
    ↓
逐K线扫描策略信号
    ↓
识别前高前低
    ↓
检测突破→回踩→再突破
    ↓
执行交易（满足条件）
    ↓
管理持仓（每根K线检查）
    ↓
检测盘整区间（2-3根波动小）
    ↓
调整止盈止损线
    ↓
触发止损/止盈
    ↓
记录交易结果
    ↓
遍历所有K线
    ↓
计算统计指标
```

---

## 三、核心算法

### 3.1 前高前低识别

```python
def find_pivot_points(df, lookback=10):
    """
    查找前高前低
    lookback: 前后多少根K线
    """
    highs = []
    lows = []

    for i in range(lookback, len(df) - lookback):
        # 检查是否为局部最高点
        if df['high'].iloc[i] == df['high'].iloc[i-lookback:i+lookback+1].max():
            highs.append({
                'index': i,
                'price': df['high'].iloc[i],
                'time': df['timestamp'].iloc[i]
            })

        # 检查是否为局部最低点
        if df['low'].iloc[i] == df['low'].iloc[i-lookback:i+lookback+1].min():
            lows.append({
                'index': i,
                'price': df['low'].iloc[i],
                'time': df['timestamp'].iloc[i]
            })

    return highs, lows
```

### 3.2 盘整区间检测

```python
def detect_consolidation(df, index, min_bars=2, max_bars=3, max_range_percent=0.01):
    """
    检测盘整区间
    min_bars: 最少K线数量
    max_bars: 最多K线数量
    max_range_percent: 最大波动范围百分比
    """
    for length in range(min_bars, max_bars + 1):
        if index < length:
            continue

        window = df.iloc[index-length+1:index+1]
        price_range = window['high'].max() - window['low'].min()
        avg_price = (window['high'].max() + window['low'].min()) / 2
        range_percent = price_range / avg_price

        if range_percent <= max_range_percent:
            return {
                'start': index - length + 1,
                'end': index,
                'high': window['high'].max(),
                'low': window['low'].min(),
                'length': length
            }

    return None
```

### 3.3 三阶段入场逻辑

```python
class TrendFollowingStrategy:
    def __init__(self, config):
        self.config = config
        self.reset_state()

    def reset_state(self):
        self.phase = 0  # 0: 等待突破, 1: 等待回踩, 2: 等待再突破
        self.breakout_high = None  # 突破K线的最高价
        self.pivot_high = None  # 突破前的前高
        self.pullback_low = None  # 回踩最低点

    def on_bar(self, df, current_index):
        if self.phase == 0:
            return self.check_breakout(df, current_index)
        elif self.phase == 1:
            return self.check_pullback(df, current_index)
        elif self.phase == 2:
            return self.check_re_breakout(df, current_index)

    def check_breakout(self, df, current_index):
        # 检测首次突破前高
        # 如果突破，记录状态进入phase 1
        pass

    def check_pullback(self, df, current_index):
        # 检测回踩
        # 最低点不跌破pivot_high
        pass

    def check_re_breakout(self, df, current_index):
        # 检测再次突破breakout_high
        # 如果突破，触发入场信号
        pass
```

---

## 四、蒙特卡洛实现

### 4.1 模拟数据生成

```python
def generate_price_path(years=1, volatility=0.02, drift=0.0001):
    """
    使用几何布朗运动生成价格路径
    years: 模拟年数
    volatility: 波动率（日）
    drift: 漂移率（日趋势）
    """
    # 4小时K线数量：365天 × 6根/天 = 2190根
    n_bars = int(years * 365 * 6)

    # 调整参数到4小时级别
    hourly_volatility = volatility / 6
    hourly_drift = drift / 6

    # 生成随机游走
    random_returns = np.random.normal(
        hourly_drift,
        hourly_volatility,
        n_bars
    )

    # 计算价格路径
    log_prices = np.cumsum(random_returns)
    prices = 100 * np.exp(log_prices)  # 起始价格100

    # 生成OHLC数据
    df = generate_ohlc_from_close(prices)

    return df
```

### 4.2 蒙特卡洛循环

```python
def run_monte_carlo(n_simulations=100):
    results = []

    for i in range(n_simulations):
        # 生成价格路径
        df = generate_price_path()

        # 运行策略
        strategy = TrendFollowingStrategy(config)
        trades = strategy.run(df)

        # 计算统计
        stats = calculate_statistics(trades, df)

        results.append(stats)

    return results
```

---

## 五、统计分析指标

### 5.1 收益率指标

- **年化收益率**: (最终余额 / 初始余额)^(1/年数) - 1
- **收益率分布**: 100次模拟的年化收益率
- **95%置信区间**: 排除最差2.5%和最好2.5%后的范围

### 5.2 风险指标

- **最大回撤**: 从最高点到最低点的最大跌幅
- **最大回撤分布**: 100次模拟的最大回撤
- **夏普比率**: (年化收益率 - 无风险利率) / 年化波动率

### 5.3 交易质量

- **胜率**: 盈利交易 / 总交易数
- **盈亏比**: 平均盈利 / 平均亏损
- **平均持仓时间**: 所有交易的平均持仓天数
- **保本率**: 成功移动止损到入场价以上的仓位比例

---

## 六、报告输出

### 6.1 文本报告

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    趋势跟踪策略蒙特卡洛回测报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 收益率统计
   平均年化收益: +28.5%
   95%置信区间: -15% ~ +65%
   最佳收益: +82%
   最差收益: -22%

📉 风险指标
   平均最大回撤: 18.3%
   95%置信回撤: 12% ~ 35%
   夏普比率: 1.42

🎯 交易质量
   平均交易次数: 45次/年
   胜率: 58%
   盈亏比: 1.85
   保本率: 72%

📈 持仓分析
   平均持仓时间: 8.5天
   满仓(3仓位)频率: 35%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6.2 图表输出

1. **收益率分布直方图**
   - X轴：年化收益率
   - Y轴：频数
   - 标记：平均值、95%置信区间

2. **最大回撤分布直方图**
   - X轴：最大回撤
   - Y轴：频数

3. **资金曲线图**
   - 前10次模拟的资金曲线
   - 显示不同模拟的表现差异

---

## 七、配置参数

```json
{
  "data": {
    "simulations": 100,
    "years": 1,
    "start_price": 100000,
    "volatility": 0.02,
    "drift": 0.0001
  },
  "strategy": {
    "lookback_bars": 60,
    "pivot_lookback": 10,
    "consolidation": {
      "min_bars": 2,
      "max_bars": 3,
      "max_range_percent": 0.01
    }
  },
  "risk": {
    "max_risk_per_trade": 0.02,
    "max_risk_positions": 3,
    "initial_capital": 10000
  }
}
```

---

## 八、下一步

1. 创建实现计划（writing-plans）
2. 设置独立工作区（using-git-worktrees）
3. 实现各个模块
4. 运行蒙特卡洛回测
5. 生成报告
