---
name: financial-market-data
description: 金融市场数据总纲。凡涉 A股、中国基金期货宏观、Polymarket 预测市场、交易行情或金融 API 查询，即当加载。
---

# Financial Market Data Canon

Use this umbrella for market and financial data retrieval. Always state source, timestamp/date, symbol mapping, and known gaps. Prefer live API output over memory.

## China market data

Use the `akcli` wrapper for AKShare data: A-shares, funds, futures, macro series, K-lines, capital flows, and financial reports. Dates should be generated dynamically or chosen as recent trading days. Avoid blocked Xueqiu APIs without tokens, and beware numeric stock symbols being coerced when the underlying API expects strings.

### Futures realtime

Use `futures_zh_realtime(symbol="品种中文名")` for live exchange quotes. The `symbol` parameter is the **中文品种名**, not the新浪标记 or contract code — pass names like `"生猪"`, `"PTA"`, `"棕榈油"`. To inspect the full list, call `futures_symbol_mark` first; its `symbol` column holds the新浪标记 (e.g. `lh_qh`) but that is **not** what `futures_zh_realtime` accepts. Contract-level series (LH2609, LH2701…) come back in the same DataFrame under the `symbol` column after filtering by product name.

## Prediction markets

For Polymarket, use the copied script/API notes when asking about markets, prices, order books, or history. Distinguish current orderbook prices from resolved outcomes and historical snapshots.

## Reporting

Return compact tables with units and dates. If an API fails or returns empty data, say so and try a nearby date/source rather than fabricating values.

## Missing / NaN data discipline

`NaN`, blank fields, and empty frames are retrieval failures, not market facts. When a missing value is material to the analysis:

1. Retry a same-family endpoint or parameter shape, preserving strings where symbols/dates must remain strings.
2. Prefer official or exchange sources next; for dynamically rendered pages, use `web_extract` first, then browser/CDP inspection, and only treat script/API endpoints as data sources after they are discovered from the page.
3. If the exact field is unavailable because a disclosure regime changed, substitute an adjacent indicator: turnover, buy/sell split, holdings value, share count, quota balance, futures-implied pricing, or ETF/flow proxies. Label the substitution.
4. Distinguish four states in the report: fact absent, not disclosed, interface failed, or proxy used. Never use a technical missing value as evidence for a substantive negative conclusion.
5. When a summary endpoint returns literal zero while the underlying detail endpoint is all `NaN` for the same field family, treat the zero as a disclosure/interface placeholder until confirmed by another source; do not write it as substantive “no flow” or “no change”.
6. If an API value is cross-checked once against the exchange source and matches within rounding, prefer the API for routine refreshes; cite the exchange check as validation rather than reloading heavy pages every time.

## Heavy exchange pages and dynamic data

Exchange pages may be heavy portals where the table is small but the surrounding site loads many assets. Do not treat a browser timeout as a data failure if traffic is still flowing or a partial snapshot exists; keep the same page/target and wait or poll. When the page reveals same-origin dynamic scripts or JSON endpoints, fetch those exact discovered URLs with the browser tool rather than enumerating guesses. Avoid parallel `browser_navigate` calls against the same browser session for data extraction; they can race the active target and inflate network traffic. If the exchange check confirms an API value within rounding, use the lighter API for future refreshes and record the exchange as validation.

See `references/exchange-dynamic-pages.md` for the concise browser-first workflow and reporting pattern.