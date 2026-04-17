---
name: baostock-cli
description: 用 baostock 查中国股市数据。查历史行情、财务指标、指数成分、宏观时用。
---

# BaoStock 调用之契

## 纲领

本 skill 以 Python import 为主径。`baostock_cli.py` 封装 BaoStock 之 `login/logout`、stdout 静默、错误检查与 `ResultSet` 解析；agent 只写业务调用与结果分析。

CLI `main()` 仅作手工探查与 smoke test，不作为主要调用方式。

## 基本用法

agent 当生成一段临时 Python，以 `call()` 取数，并在同段代码中解析、筛选、汇总：

```python
from baostock_cli import call

rows = call(
    "query_history_k_data_plus",
    code="sh.600519",
    fields="date,open,high,low,close,volume",
    start_date="2026-06-01",
    end_date="2026-06-05",
    adjustflag="2",
)

result = [
    {"date": row["date"], "close": row["close"]}
    for row in rows
]
print(result)
```

辅助探查：

```python
from baostock_cli import apis, info
```

- `apis(keyword="")`：列可调用 API
- `info(name)`：查文档与参数
- `call(name, **kwargs)`：调用 API，返回 Python 数据；`ResultSet` 归一为 `list[dict]`

## 运行方式

```bash
uv --directory /home/josephx/code/agent-skills/common/baostock-cli run python script.py
```

若只需手工验通：

```bash
uv --directory /home/josephx/code/agent-skills/common/baostock-cli run python baostock_cli.py --list trade
```

## 核心 API 速查

### 股票数据
| 功能 | API | 关键参数 |
|------|-----|----------|
| 历史K线 | `query_history_k_data_plus` | code(sh.600519), fields, start_date, end_date, frequency(d/w/m), adjustflag(1后/2前/3不) |
| 股票基本信息 | `query_stock_basic` | code, code_name |
| 复权因子 | `query_adjust_factor` | code, start_date, end_date |
| 行业分类 | `query_stock_industry` | 无 |
| 交易日历 | `query_trade_dates` | start_date, end_date |

### 财务数据（季频）
| 功能 | API | 关键参数 |
|------|-----|----------|
| 偿债能力 | `query_balance_data` | code, year, quarter |
| 盈利能力 | `query_profit_data` | code, year, quarter |
| 成长能力 | `query_growth_data` | code, year, quarter |
| 营运能力 | `query_operation_data` | code, year, quarter |
| 现金流量 | `query_cash_flow_data` | code, year, quarter |
| 杜邦分析 | `query_dupont_data` | code, year, quarter |
| 业绩预告 | `query_forecast_report` | code, year, quarter |
| 业绩快报 | `query_performance_express_report` | code, year, quarter |
| 分红送配 | `query_dividend_data` | code, year, quarter |

### 指数与宏观
| 功能 | API | 关键参数 |
|------|-----|----------|
| 沪深300成分股 | `query_hs300_stocks` | 无 |
| 上证50成分股 | `query_sz50_stocks` | 无 |
| 中证500成分股 | `query_zz500_stocks` | 无 |
| 存款利率 | `query_deposit_rate_data` | 无 |
| 贷款利率 | `query_loan_rate_data` | 无 |
| 存款准备金率 | `query_required_reserve_ratio_data` | 无 |
| 货币供应量(月) | `query_money_supply_data_month` | 无 |
| 货币供应量(年) | `query_money_supply_data_year` | 无 |

## 注意

- 日期格式为 `YYYY-MM-DD`
- 股票代码格式为 `sh.600519` / `sz.000001`
- 参数默认以字符串传入，除非 BaoStock 明确要求数值
- `call()` 已自动 login/logout；业务代码不得重复登录
