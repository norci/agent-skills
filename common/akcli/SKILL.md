---
name: akcli
description: 用 akshare 取数前：akshare 的取数接口与参数。
---

# 行情数据之取

## 核心

`call_api(func_name, **kwargs)` 调 akshare API，返回 pandas DataFrame。

Python 取数宜在技能目录执行：`cd <技能目录> && uv run python ...`。

## 用法

LLM 生成 Python 代码，`from akcli.cli import call_api` 调用之。

```python
from akcli.cli import call_api

df = call_api("stock_zt_pool_em", date=20260317)
print(df.nlargest(5, "涨跌幅")[["名称", "涨跌幅"]].to_string(index=False))
```

常用场景：

- 指数：`call_api("stock_zh_index_spot_sina")`
- 日K：`call_api("stock_zh_a_hist", symbol="600519", period="daily", start_date="20260301", end_date="20260317", adjust="qfq")`
- 宏观：`call_api("macro_china_cpi")`

日期格式 `YYYYMMDD`。

## 不可用 API

`*_xq` 系列（雪球）需 `xq_a_token`，当前环境不具备。`src/akcli/data/blocked.json` 记着每个被拦 API 的替代者（如 `stock_zh_index_spot_em` → `stock_zh_index_spot_sina`、`fund_etf_spot_em` → `fund_etf_spot_ths`）。`call_api` 命中被拦项时抛 `RuntimeError`，按该表改用替代 API。

## 常用 API

| 功能 | API | 主要参数 |
| 指数行情 | `stock_zh_index_spot_sina` | — |
| 日K/周K/月K | `stock_zh_a_hist` | symbol, period, start_date, end_date, adjust |
| 涨停股池 | `stock_zt_pool_em` | date |
| 跌停股池 | `stock_zt_pool_dtgc_em` | date |
| ETF行情 | `fund_etf_spot_ths` | — |
| 个股新闻 | `stock_news_em` | symbol |
| CPI/PPI/GDP | `macro_china_cpi / _ppi / _gdp` | — |

## 注意

- 返回 DataFrame，以 pandas 处理之
