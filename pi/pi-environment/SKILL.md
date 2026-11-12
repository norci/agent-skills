---
name: pi-environment
description: fabric_exec 的工具入口、往返成本、payloads 与 TODO 建法。写 fabric_exec 程序时用。
---

# pi 环境

环境不设时间限制、轮次上限与评分。

## 工具入口

fabric 工具入口按来源分三类：pi 核心工具走 `pi.<名>`，pi 扩展走 `extensions.<名>`，pi 的 MCP 工具写成 `extensions.mcp__<server>__<tool>`。

## 工具选择

- agent 搜索用 `extensions.web_search`，取正文用 `extensions.crw_extract_sync`。GitHub 用 gh。计算用 codemode。
- agent 用 pi 内置工具 ls/read/find/grep 等。代码定位、查引用、改名走 `agent-lsp-navigation` skill：符号由 LSP 解析，grep 只认字面文本。`pi.bash` 只用于运行外部程序。
- `pi.bash` 把空 stdout 返回成 "(no output)"。

## 一步一程序

- 一次 `fabric_exec` 是一次真实往返，它重发全量上下文并产生首 token 延时。往返次数即成本，与本次返回长短无关。上下文里已有的东西，agent 直接取用。
- 一个程序即一步之全部：取证据、判判据、按判据续取、落动作、复核，agent 在同一程序里走完。无依赖者同批派出，await 只用于有依赖者。判据在程序里判，不通过即在本程序内换判据重算，程序只 return 结论和证据。
- 程序只在两种情况下结束：需要用户定夺，或需要重读尚未进上下文的一整段材料。

## payloads

- 代码体出现换行、反引号、`"`/`'`、`${`、`\`、heredoc 任一，agent 就把正文整段放进顶层 payloads，代码体只写 `π.<key>`。这条规则管全部代码体：bash、edit 的 newText、write、compress 正文，命中即走。agent 改文件前先数锚点命中数，命中一处才改。

## 长命令与后台任务

- 结果要用来续做时，前台跑并显式给 `timeout`（秒）。不传则由外层截断，实测六十秒被杀，日志尾写「Command timed out after 60 seconds」，前面看似在跑。
- 结果不影响本回合续做时才 `background: true`；派出即结束回合，完成事件唤醒 agent，不另起一次去等。
- 后台任务在程序内等不到：fabric_exec 的全局里没有 `tasks`，写 `tasks.wait` 报 `Cannot find name 'tasks'`。故要等就别派后台。
- 派出后不查状态。`tools.call({ref:"tasks.get"})` 只在不打算等、要决定停不停时读一次。

## TODO

用 `extensions.todo` 时，agent 先建 TODO 后动手，一步一条。description 写清原因、文件、判据、陷阱。agent 开始一条时标 in_progress，验证通过后标 completed。
