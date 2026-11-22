---
name: batch-processing
description: 第一个工具调用前：把已知的多步工具链压进最少的 turn，不要一步步往返。
---

## 目的

减少 turn 数。每个 turn 有固定延迟；步骤已清楚的链必须并进一次调用，而不是逐步发出。

## 先分两类

- 探索：下一步的读取位置本身未知，必须靠上一读数才能定。允许一次一个读；读到能定下一步就停。
- 已知链：读取位置和步骤都已清楚（例如任务记录或压缩摘要里已给出文件的行号与符号），例如 编辑 → ruff → pytest → md5 → 提交。必须批量，用下节机制。
- 已知位置的多个窗口算已知链，不算探索：一次 parallel 全读完。拿「下一步取决于上一步」当借口分四五轮读，是违例。

## 批量机制（按序选）

- 互不依赖的调用（读多个文件、改不同文件或不重叠区域、多个 LSP safe_edit）放进一个 `multi_tool_use.parallel` 块。
- 有依赖的 shell 链放进一个 `shell.run`：`set -e` 串行，末尾只打印判据结论行。中途失败即停，不会误提交。
- 同一文件的多处编辑按原行号在一条 `resource.edit` 里发多个操作，避免多次往返。
- 不要用 Lisp REPL 定义“判定函数”再单独调用。纯 Lisp 的 `pmap` 不调用真实工具，只会多出写文件、跑文件两个 turn，真实工具最终仍逐个发出。

## 先读全，再改全

`resource.edit` 按原行号和 revision 定位：一次编辑后，之前读到的行号与 revision 全部失效。流程固定为：先把所有要改的窗口在一次 parallel 里读全，再把所有编辑在一次 parallel 里发完， editing 与 reading 不穿插。中途回头补读，会撞上「lines not fully visible under this revision」，白费两轮。

优先用 LSP `safe_edit`（按文本匹配，不依赖行号与 revision），把跨文件的编辑放同一 parallel 块；它还能给出 `net_delta` 作安全判据。手改再回退更贵，别走这条路。

## 判据即数据

把通过条件写进链本身：ruff 退出码、pytest 读 `.report.json` 的 `summary`、md5 比对、`git diff --check`。链只回结论和必要数值，不回中间输出。中间结果留在 shell 日志或文件里，不进对话。

## 收尾条件

只有用户决策、缺输入、缺授权、闸失败才结束 turn。否则把剩余步骤并进下一批。

## LSP 编辑

用 `safe_edit`（完整路径 + `old_text`/`new_text`，`net_delta=0` 为安全）。不同文件的编辑放同一个 parallel 块。
