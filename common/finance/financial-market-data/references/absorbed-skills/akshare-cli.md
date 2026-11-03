---
name: akshare-cli
description: 使用 akcli 模块查询中国金融市场数据（A股、基金、期货、宏观经济等）。当用户询问股票行情、K线、资金流向、基金净值、宏观经济数据、财务报表时使用。
categories: [akshare]
---

# 行情数据之取

## 核心

直接调 `akcli.sh`（壳指令）或 `.venv/bin/akcli`，均回 JSON。`call_api()` 需在 `.venv` Python 下执行，系统全局 Python 不见 `akcli` 包。

## 用法（壳指令）

```bash
# 目录内直接调用
cd /home/josephx/code/agent-skills/common/akcli
./akcli.sh stock_zt_pool_em date=20250317
./akcli.sh --list 涨停
./akcli.sh --info stock_zh_index_spot_sina
```

## 用法（Python 式，须进 venv）

```bash
/home/josephx/code/agent-skills/common/akcli/.venv/bin/python -c "
from akcli.cli import call_api
df = call_api('stock_zt_pool_em', date=20250317)
print(df.head())
"
```

期间不要无谓套 venv——脚本本身已是 thin wrapper，再套一层徒增困扰。

## 日期

日期必须动态生成，禁止硬编码。

```python
import subprocess
today = subprocess.check_output(["date", "+%Y%m%d"]).decode().strip()
```

## 不可用 API

`*_xq` 系列（雪球）需 `xq_a_token`，当前环境不具备。

已在 `blocked.json` 登记，会被自动拦截：

- `stock_individual_spot_xq`
- `stock_individual_basic_info_xq`
- `stock_individual_basic_info_hk_xq`
- `stock_individual_basic_info_us_xq`

## 参数转换陷阱

`call_api` 会把数字串自动转 int。`symbol` 如 `"600519"` 会被转成 `600519`，造成 akshare 内部 `.startswith()` 失败。当前规避：**不用 `stock_zh_a_hist`**，改用 spot 或 index 类 API。

## 常用 API

| 功能 | API | 主要参数 |
|------|-----|----------|
| 指数 | `stock_zh_index_spot_sina` | — |
| 日K | `stock_zh_a_hist` ⚠️ | symbol, period, start_date, end_date, adjust |
| 涨停 | `stock_zt_pool_em` | date |
| 跌停 | `stock_zt_pool_dtgc_em` | date |
| ETF | `fund_etf_spot_ths` | — |
| 个股新闻 | `stock_news_em` | symbol |
| 宏观 | `macro_china_cpi / _ppi / _gdp` | — |

日期格式 `YYYYMMDD`。

## 检索

```bash
akcli.sh --list <关键词>
akcli.sh --info <api_name>
```