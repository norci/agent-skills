---
name: batch-processing
description: 第一个工具调用前：把已知的多步工具链压进最少的 turn，不要一步步往返。
---

## 目的

减少 turn 数。每个 turn 有固定延迟；步骤已清楚的链必须并进一次调用，而不是逐步发出。

## 先分两类

- 探索：下一步取决于上一步的读数。允许一次一个读；读到能定下一步就停。
- 已知链：步骤与依赖都已清楚（例如 编辑 → ruff → pytest → md5 → 提交）。必须批量，用下节机制。

## 批量机制（按序选）

- 互不依赖的调用（读多个文件、改不同文件或不重叠区域、多个 LSP safe_edit）放进一个 `multi_tool_use.parallel` 块。
- 有依赖的 shell 链放进一个 `shell.run`：`set -e` 串行，末尾只打印判据结论行。中途失败即停，不会误提交。
- 同一文件的多处编辑按原行号在一条 `resource.edit` 里发多个操作，避免多次往返。
- 不要用 Lisp REPL 定义“判定函数”再单独调用。纯 Lisp 的 `pmap` 不调用真实工具，只会多出写文件、跑文件两个 turn，真实工具最终仍逐个发出。

## 判据即数据

把通过条件写进链本身：ruff 退出码、pytest 读 `.report.json` 的 `summary`、md5 比对、`git diff --check`。链只回结论和必要数值，不回中间输出。中间结果留在 shell 日志或文件里，不进对话。

## 收尾条件

只有用户决策、缺输入、缺授权、闸失败才结束 turn。否则把剩余步骤并进下一批。

## LSP 编辑

用 `safe_edit`（完整路径 + `old_text`/`new_text`，`net_delta=0` 为安全）。不同文件的编辑放同一个 parallel 块。
