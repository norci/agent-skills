---
name: agent-lsp-navigation
description: 打开源码或查调用关系前：符号导航的点边判据与走查顺序。
---

## 点与边

「这个符号是什么、在哪、怎么写的」是点；「谁用它、谁测它、改它牵连谁」是边。边只由边工具答。

本轮每一步先判它是点还是边，再选一次能答完它的调用。找得到而不用，或拿若干点工具的原文自行接线，那一步就是绕行。

`.lisp` 走 `lisp-ast` 与 `lisp.apropos` / `lisp.source`；本套服务没有 Common Lisp 后端。

## 走查顺序

输入一个行为或符号名，输出结论与所据之符号、文件、边。

1. `list_symbols` 取符号树，从树里取名字写锚，不猜名字。
2. `explore_symbol` 一次取签名、源码、调用者、引用、测试者。
3. 沿边扩展：`callers` 看上下游，`blast_radius` 看牵连面，`get_tests_for_file` 看测试文件。问「谁测了这个符号」仍用 `explore_symbol`。`blast_radius` 的 `filter: 'untested'` 在 Python 上把局部变量也算符号，测试面按单符号 `find_references` 判。
4. 只对要下结论的符号取 `get_symbol_source`；取的次数等于要核的符号数，多一次都是手工拼边。
5. 只读走查到此收手：写出结论与所据之符号、边。
6. 要改才续：试改（模拟会话链或一步 `safe_edit` 看净增量）、落改动、跑项目自己的检查命令。

只读调用并发。改状态的调用串行：前一个返回后再发下一个；串行只约束次序，一条编辑链在一轮内走完。

## 落改动

- 单段替换用 `safe_edit`；同文件多段非重叠改动合成一个 `WorkspaceEdit` 一次 `apply_edit`。只有后一处依赖前一处的返回值、或两段区间重叠时才拆。
- `replace_symbol_body` 的 `new_body` 只给定义行之后的行；多行参数的签名会被折断，这类函数改整段替换。`insert_after_symbol` 的 `code` 给完整定义行。
- CJK 文本附近改名或替换函数体后，改后定义数与文件行数须同改前一致，诊断返回为空不作落对证据。
- 按字符串接线的框架里，改名后用框架的图接口或全项目旧名扫描收残，逐个定点改，框架检查通过才算接线改完。
- 改名或删除前先问边；符号一删就再没有提问对象。改名先 `dry_run` 看落点，去掉 dry_run 直接改盘。
- 新文件无符号可锚：先落全文，此后按符号改。`blast_radius` 与 `detect_changes` 不计未跟踪的新文件。
- 模拟会话链 `NetDelta=0` 只证明服务没推新诊断；pyright 不推，故不构成证据，仍以项目检查命令判。
- `commit_session` 一返回就把会话置为 committed，`apply: false` 也一样；用完 `destroy_session` 释放。

## 返回信封

正文在 `content[0].text`；符号字段只在正文里，`.details` 只有 `server` 与 `tool` 两键。`String(result)` 得 `[object Object]`。

- `GCF profile=generic`：键值块，或 `## [N]{列名}` 表格，首列是行号，`N` 是条数。
- `GCF profile=graph`：`targets` / `related` / `edges` 三段。`@k fn pkg.name 1.00 lsp_resolved` 一行一节点；`@1<@2 calls` 读作「@2 调用 @1」。带 `lsp_resolved` 的边由服务解析，其余为推断。首行 `symbols=N edges=M` 决定要不要细看。
- `Source` 是该符号在文件里的整段原文，不 `read` 复核。`StartLine` 带装饰器时指最外层装饰器行，定义行由 `Source` 里首个 `def` / `class` 行定。
- `detect_changes` 的正文是 `targets` 全表，一行一符号，不分风险级；判风险要读 `related` 与调用方。

## 锚的落点

- `position_pattern` 以源码里一行作锚、`@@` 收尾。同前缀者会抢锚，每次读回 `SymbolName=` 核对，与所问名字不等即换锚；签名片段作锚会落到参数上；同名跨类取该类内独有的一行。
- `line` 与 `column` 落在标识符本身且落在定义行。落在 `def` 关键字列、函数体、注释、装饰器行都不抛错，只回不相干的命中或空结果。行号随编辑移动，改过文件后重取符号树或改用锚。

## 边没查到时

引用回 0 条、牵连面回 `symbols=0`、诊断回空，都不等于「没有调用者」「没有牵连」「文件干净」。先报出服务名与文件，把这一层失败写进回答，再决定是否换路。

- 按参数名接线的框架里节点之间没有一次调用，服务认不出这条边；`symbols=0` 且正文带 `indexed=true` 读作「这张图里没有调用边」，不是「没人用」。接线面问框架自己的图。
- 服务未起、仍在建索引、或该工具不在 `SupportedTools` 里，空结果不作证据。
- 内置构建与测试命令不读项目配置；取真错用项目自己的检查命令。
- 任何从 LSP 退到读文件或 grep 的动作，先说出缺的是哪一层；说不出即不换。

## 起服务

先 `detect_lsp_servers` 看已装服务，再 `start_lsp` 指到项目根；`language_id` 指名缺二进制的语言即整体失败。路径取绝对路径且落在已注册根内。

`start_lsp` 是累加，不是替换；换 root 再调一次，按名查找会扇出到全部服务、混进同名符号，故找定义用符号树写锚。`restart` 会把服务弄死；卡死就停进程后重起。
