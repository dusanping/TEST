# Host Load Analyzer (CPU + Disk)

这个项目是一个可扩展的 Python 工程，用于：

1. 基于 PromQL 采集主机 CPU / 磁盘时序。
2. 做通用异常检测（阈值 + robust z-score）。
3. 做容量趋势预测（线性回归估算到达阈值时间 ETA）。
4. 按组件维度扩展后续逻辑（保留 `MetricCollector.collect_component_metrics` 的通用入口）。

---

## 对你给的两张图的快速判断

> 说明：你文字里写了“第一张是cpu，第一张是磁盘”，按上下文应为“第一张 CPU，第二张磁盘”。

### 图1（CPU）
- 在 17:23 左右前后存在明显异常形态：先接近 0%，随后瞬间拉升到 80~92%，再快速跌回低位。
- 这种“阶跃 + 快速回落”通常要排查：
  - 指标采集/标签切换（ident 或 primary_ip 变更）；
  - 任务瞬时突发（批任务、压测、GC 风暴）；
  - 指标口径（avg_over_time 窗口长度变化）导致视觉跳变。
- 风险判定：
  - 如果高位持续 >15~30 分钟，属于高风险 CPU 饱和；
  - 如果仅短脉冲，优先按“告警观察 + 根因排查”处理。

### 图2（磁盘）
- 前段在 80~95% 高位，随后出现断崖式降到 ~12%，之后缓慢上升到 ~24%。
- 这通常意味着：
  - 发生了清理/扩容/切盘；
  - 或者监控对象切换导致时间序列不连续。
- 容量趋势：
  - 当前 12%->24% 为缓慢增长，短期到 85% 风险低；
  - 仍应计算斜率并给出 ETA（本项目自动给）。

---

## 架构

```text
src/host_load_analyzer/
  clients/monitor_client.py    # 鉴权 + PromQL range 查询
  components/promql.py         # CPU/磁盘 PromQL 构造
  components/collector.py      # 通用组件采集入口（便于扩展）
  core/analyzer.py             # CPU+磁盘统一分析
  core/anomaly.py              # 异常检测
  core/forecast.py             # 容量预测 ETA
  core/models.py               # 数据模型
  utils/series.py              # 时序工具函数
  cli.py                       # 命令行入口
```

---

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 配置

默认读取环境变量：

- `MONITOR_BASE_URL`
- `MONITOR_USERNAME`
- `MONITOR_PASSWORD`
- `ES_METRICS_ID`（可选）

并写入 `host_load_analyzer.config.settings.MONITOR_CONFIG`。

---

## 使用

```bash
host-load-analyzer \
  --host bjx-152-22-42.linux.17usoft.com \
  --primary-ip 10.152.22.42 \
  --mountpoint / \
  --hours 48 \
  --data-source v2_metrics
```

输出包含：
- CPU / 磁盘统计摘要（avg/p50/max/min）；
- 异常点列表（时间、值、原因、级别）；
- 线性趋势容量预测（到阈值 ETA）。

---

## PromQL 鉴权与查询（按你给的参考实现）

核心流程：
1. `POST /oauth/systemLogin` 获取 token；
2. `GET /prom/redirect/{tsdbid}/api/v1/query_range` 或 `/prom/redirect/api/v1/query_range`；
3. 请求头带 `x-token`；
4. 参数传 `query/start/end/step`。

项目中的 `MonitorClient` 即按此实现，并保留 token 缓存。

---

## 异常检查通用方法

组合策略：
1. **硬阈值**（例如 CPU>85%、Disk>90%）；
2. **Robust Z-Score**：
   - 中位数 `median`；
   - MAD = `median(|x - median|)`；
   - `robust_z = 0.6745 * (x - median) / MAD`；
3. 触发任一条件即标记异常。

优点：
- 对脏数据、尖峰更稳健；
- 比单纯均值/标准差更适合运维指标。

---

## 容量预测通用方法

使用最小二乘线性回归估算斜率（单位：每小时变化率）：

- `slope_per_hour > 0` 时：
  - `ETA = (threshold - current) / slope_per_hour`
- `slope_per_hour <= 0` 时：
  - 视为短期不会达到阈值（ETA = None）

建议：
- 生产可升级成分段回归、Holt-Winters、Prophet 等；
- 加上“节假日/业务周期”特征会更稳。

---

## 扩展到组件维度

后续如果要分析 Redis/ES/MySQL 等组件，只需：

1. 在组件层新增 PromQL 模板；
2. 用 `MetricCollector.collect_component_metrics()` 统一拉数；
3. 复用 `anomaly.py` + `forecast.py` 输出一致报告。

