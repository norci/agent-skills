# Exchange dynamic pages: browser-first extraction notes

Use when an exchange/market-data page is a heavy portal and the table is populated by JavaScript.

## Lessons

- A browser navigation timeout is not proof that the data is absent. If the user or logs indicate the site is still transferring data, keep the page/target alive and poll rather than restarting navigation.
- `NaN` or blank table fields are interface state, not market evidence. For material fields, seek an official/nearby source or a labeled proxy.
- Prefer the browser tool chain when the task is browser/CDP inspection. Shell `curl` is acceptable only for explicit endpoint health checks or when the user asks for it; it should not become the primary browser path after a correction.
- Avoid parallel navigation calls in one browser session while extracting data. They can switch the active target and corrupt subsequent `console`/snapshot reads.
- Once the page reveals exact same-origin dynamic scripts/JSON endpoints, navigate to those exact URLs with the browser tool; do not enumerate speculative endpoint names, because miss URLs may return full branded error pages and waste bandwidth.

## Reporting pattern

Report exact source URL, timestamp/date embedded in the script/table, units, and whether the value is exact, proxy, or merely quota/availability metadata. If a disclosure regime no longer exposes a field, say "not disclosed by this source" and name the substitute indicator.
