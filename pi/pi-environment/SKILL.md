---
name: pi-environment
description: codemode 程序的往返成本、并行写法与 TODO 建法。写 codemode 程序时用。
---

# pi 环境

环境不设时间限制、轮次上限与评分。

## 一步一程序

- 一次 `codemode` 是一次真实往返，它重发全量上下文并产生首 token 延时。往返次数即成本，与本次返回长短无关。上下文里已有的东西，agent 直接取用。
- 一个程序即一步之全部：取证据、判判据、按判据续取、落动作、复核，agent 在同一程序里走完。无依赖者 `Promise.allSettled` 同批派出，await 只用于有依赖者。
- 程序只在两种情况下结束：需要用户定夺，或需要取回尚未进上下文的一段非代码材料。

## bash

- 结果要用来续做时前台跑并显式给 `timeout`（秒）。不传则由外层截断，实测六十秒被杀，日志尾写「Command timed out after 60 seconds」，前面看似在跑。
- `tools.bash` 回 `{ output, exit_code, truncated, full_output_path?, wall_time_seconds }`；非零退出是结果不是异常。空 stdout 回空串。

## TODO

用 `todo` 时，agent 先建 TODO 后动手，一步一条。description 写清原因、文件、判据、陷阱。agent 开始一条时标 in_progress，验证通过后标 completed。
