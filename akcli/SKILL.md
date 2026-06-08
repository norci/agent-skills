---
name: akshare-cli
description: 使用 akcli 模块查询中国金融市场数据（A股、基金、期货、宏观经济等）。当用户询问股票行情、K线、资金流向、基金净值、宏观经济数据、财务报表时使用。
---

# 行情数据之取

## 核心

`call_api(func_name, **kwargs)` 调 akshare API，返回 pandas DataFrame。

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
- 实时（雪球）：`call_api("stock_individual_spot_xq", symbol="SH688295")` — 返回两列（item/value），以 `dict(zip(df["item"], df["value"]))` 转为字典取用
- 宏观：`call_api("macro_china_cpi")`

日期格式 `YYYYMMDD`。搜索 API 与查看参数用 `akcli.sh --list <关键词>` / `akcli.sh --info <api_name>`。

## 常用 API

| 功能 | API | 主要参数 |
|------|-----|----------|
| 指数行情 | `stock_zh_index_spot_sina` | — |
| 日K/周K/月K | `stock_zh_a_hist` | symbol, period, start_date, end_date, adjust |
| 涨停股池 | `stock_zt_pool_em` | date |
| 跌停股池 | `stock_zt_pool_dtgc_em` | date |
| ETF行情 | `fund_etf_spot_ths` | — |
| 个股新闻 | `stock_news_em` | symbol |
| CPI/PPI/GDP | `macro_china_cpi / _ppi / _gdp` | — |

## 注意

- 返回 DataFrame，以 pandas 处理之
