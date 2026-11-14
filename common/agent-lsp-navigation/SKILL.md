---
name: agent-lsp-navigation
description: LSP 符号导航——按符号取源码、查调用者与类型层级、算影响面、模拟编辑的工具形状与返回信封。凡要读、找、改 .py/.ts/.go/.rs 源码，动手之前先读本技能；先 grep 或先整文件 read 即属绕行。
---

## 点与边分属两类工具

「这个符号是什么、在哪、怎么写的」是点，「谁用它、谁测它、改它牵连谁」是边。原文里没有边，拼不出来：拿点工具答边的问题就是绕行。

| 用途 | 工具 |
| --- | --- |
| 点 | `list_symbols`、`get_symbol_source`、`inspect_symbol`、`find_symbol`、`go_to_symbol`、`get_symbol_documentation` |
| 边 | `explore_symbol`（`explore` 同义）、`callers`、`find_callers`、`find_references`、`get_document_highlights`、`type_hierarchy`、`go_to_implementation`、`go_to_definition`、`go_to_declaration`、`go_to_type_definition`、`get_cross_repo_references`、`blast_radius`、`detect_changes`、`get_tests_for_file` |
| 改 | `safe_edit`（`safe_apply_edit` 同义）、`apply_edit`、`replace_symbol_body`、`insert_before_symbol`、`insert_after_symbol`、`safe_delete_symbol`、`rename_symbol`、`refactor`、`suggest_fixes` |
| 试与验 | `create_simulation_session`、`simulate_edit`、`simulate_chain`、`evaluate_session`、`commit_session`、`discard_session`、`destroy_session`、`preview_edit`、`get_diagnostics`、`get_completions`、`format_document`、`format_range`、`get_inlay_hints`、`get_semantic_tokens` |
| 会话 | `start_lsp`、`restart_lsp_server`、`detect_lsp_servers`、`open_document`、`close_document`、`add_workspace_folder`、`list_workspace_folders`、`remove_workspace_folder`、`set_log_level`、`get_server_capabilities`、`activate_skill`、`get_skill_phase`、`deactivate_skill`、`did_change_watched_files`、`import_cache`、`export_cache`、`run_build`、`run_tests` |

判据：本轮手工做的每一步，先在这张表里找一件能答它的工具；找得到而不用，那一步就是绕行。

## 串行不等于分轮

改状态的调用必须串行：前一个返回后再发下一个，不得并发。

串行只约束调用之间的次序，不约束轮次。不要把一条编辑链拆成多轮；同一轮内可以连续发出多个串行调用，编辑链在一轮内走完。

同一文件的多个非重叠改动先合成一个 `WorkspaceEdit`，一次 `apply_edit` 发出；`safe_edit` 只做单段连续替换。只有后一处依赖前一处的返回值，或两段区间重叠时，才拆成串行调用。

## 一问一调用

能从上表答出的问题，不许 grep，不许整文件 read。

| 问什么 | 一次调用 | 回什么 |
| --- | --- | --- |
| 这个符号是什么、谁用它、有没有测试 | `explore_symbol` | 签名 + 源码 + 调用者 + 引用 + 测试者 |
| 改这几个文件会牵连谁 | `blast_radius` | 按 test / non-test 分区的调用者；`filter: 'untested'` 在 Python 上把局部变量也算符号，结果不具判别力，测试面按单符号 `find_references` 判 |
| 谁调这个函数、这个函数调了谁 | `callers({ direction })` | 调用者图、被调者图 |
| 类与接口的父子关系 | `type_hierarchy` | `extends` / `implements` 边 |
| 接口或抽象方法有哪些实现 | `go_to_implementation` | 实现清单；pyright 不支持 |
| 文件里有什么 | `list_symbols({ format: 'outline' })` | 符号树，含方法、字段与行号 |
| 一个符号的源码 | `get_symbol_source` | `StartLine` / `EndLine` / `Source` |
| 这个函数收什么参数 | `inspect_symbol` | 签名与文档；`get_signature_help` 在 pyright 上回 `null` |
| 标准库或依赖里某符号的文档 | `get_symbol_documentation` | 工具链原文；只认该工具能解析的全名 |
| 本文件里这个变量在哪读、在哪写 | `get_document_highlights` | 全文件读写点，`Kind` 2=读 3=写 |
| 这段改动会不会坏 | `safe_edit` 的 `net_delta` 或模拟会话链 | 诊断增量（见「改与试」） |
| 按名字改代码 | `replace_symbol_body` / `insert_*_symbol` | 定位靠符号树，不靠行号 |
| 改名 | `rename_symbol({ dry_run: true })` | 逐文件的替换区间 |
| 提交前看未提交改动的影响 | `detect_changes` | 按 high / medium / low 分级的受影响符号 |
| 同包有哪些测试文件 | `get_tests_for_file` | 按目录约定；问「谁测了这个符号」用 `explore_symbol` |
| 跨仓谁用了这个符号 | `get_cross_repo_references` | 按仓库分区的引用边 |
| 按名字找定义，不知在哪个文件 | `find_symbol` | 只认裸名，`类.方法` 回 0 条 |
| 这个位置能做什么重构、什么快速修复 | `refactor`（不带 `action`）、`suggest_fixes` | 清单；标题须与清单逐字相同 |
| 服务支持哪些工具、缺哪些 | `get_server_capabilities` | `SupportedTools` / `UnsupportedTools`；不在前者里的工具不调，它的空结果不当证据 |

## 一轮开发的顺序

输入：本轮要改的行为或符号名。输出：改动落盘且项目检查命令通过。

```
1. 定位   list_symbols({ file_path, format: 'outline' }) -> 符号树；从树里取名字写锚，不猜名字
2. 读懂   explore_symbol({ position_pattern }) -> 签名 + 调用者 + 引用 + 测试者
3. 取原文 只对本轮要改的符号 get_symbol_source，一次一个，取完即改
4. 查牵连 blast_radius({ changed_files: [单个文件] }) -> 按 test / non-test 分区
5. 试改   模拟会话链，或一步 safe_edit 看 net_delta
6. 改     单段 safe_edit / replace_symbol_body / insert_*_symbol / rename_symbol；同文件多段非重叠改动合成一个 WorkspaceEdit 走 apply_edit
7. 验     项目自己的检查命令（uv run pyright / bunx tsc --noEmit / go build）
```

这七步在一轮内走完；第 3 步取原文与第 6 步落改动都是串行调用，不是分轮。

- 本轮 `get_symbol_source` 的次数等于本轮要改的符号数，多出来的每一次都是手工拼边。
- 新文件无符号可锚：先 `write` 落全文，此后按符号改。
- `blast_radius` 与 `detect_changes` 不计未跟踪的新文件，新文件的影响面指名路径再问一次。

## 返回值

每个工具回 MCP `CallToolResult`，正文在 `content[0].text`；`String(result)` 得 `"[object Object]"`。符号字段只在正文里，`.details` 只有 `{ server, tool }` 两键。

- `GCF profile=generic`：键值块（`StartLine=96`），或 `## [N]{列名}` 表格，首列是行号，`N` 即条数。
- `GCF profile=graph`：`## targets` / `## related` / `## edges`。`@k fn pkg.name 1.00 lsp_resolved` 一行一个节点，`@1<@2 calls` 读作「@2 调用 @1」；首行 `symbols=N edges=M` 决定要不要细看。带 `lsp_resolved` 的边是服务解析的，其余为推断。
- `Source` 就是该符号在文件里的整段原文，行数等于 `EndLine - StartLine + 1`；不 `read` 复核。
- `StartLine` 带装饰器时指最外层装饰器行，定义行 = `StartLine` 加 `Source` 里首个 `def` / `class` / `async def` 行的下标；装饰器可跨多行，不能用「固定加一」。

- `detect_changes` 的正文是 `## targets` 全表，一行一个符号，不分风险级；要判风险得读 `related` 与各符号的调用方，不能拿这张表当摘要。

## 位置怎么给

收 `position_pattern` 的：`find_references`、`inspect_symbol`、`get_symbol_source`、`rename_symbol`、`explore`、`explore_symbol`、`refactor`。

只收 `line` + `column`（1 起算）的：`callers`、`find_callers`、`go_to_declaration`、`go_to_implementation`、`go_to_type_definition`、`go_to_definition`、`type_hierarchy`、`prepare_rename`、`suggest_fixes`、`get_document_highlights`、`get_signature_help`、`get_completions`。

`position_pattern` 把源码里的一行作锚，以 `@@` 收尾：

- 先 `list_symbols` 看符号树再选锚；猜出来的名字报 `position_pattern not found in file`。
- 同前缀者会抢锚：`load` 与 `load_all` 并存时 `'def load@@'` 回 `load_all`。每次读正文的 `SymbolName=`，与所问名字不等即换锚。
- 同名跨类时 `SymbolName` 证明不了身份，锚取该类内独有的一行原文。
- 签名片段作锚会落到参数上：`'def load(path@@'` 回 `SymbolName=path`。

`line` / `column` 必须落在标识符本身且落在定义行。落在 `def` 关键字那一列、函数体、注释、接收者括号上都不抛错，只回 `No call hierarchy item found at <path>:<line>:<col>` 或 `lsp error 0: identifier not found`。`type_hierarchy` 只认类型名，落在函数上回 `lsp error 0: not a type name`。行号随编辑移动，改过文件后重取符号树或改用 pattern 锚。`find_references` 落在装饰器行或 `class` 关键字那一列，回的是全仓同名 import 行之类的无关命中（实测 57 条）；落在类名那一列才得真实引用（实测 56 条）。

## 会话

```
start_lsp({ root_dir: '/abs/project', language_id: 'python' })
```

- `language_id` 指名缺二进制的语言即整体失败；先 `detect_lsp_servers({ workspace_dir })` 看 `InstalledServers`。
- `start_lsp` 是累加，不是替换：换 root 再调一次，旧服务仍挂着，`find_symbol` / `go_to_symbol` 会扇出到全部服务、混进别的项目的同名符号。找定义用 `list_symbols` 的符号树写锚。
- 路径必须绝对且落在已注册工作区内；相对路径按进程 cwd 解析，回 `is outside workspace root`。
- 未起服务时其余工具回 `LSP client not initialized; call start_lsp first`。刚起服务时 `find_references` / `blast_radius` 可能回 `workspace is still being indexed`，等 1 秒重试。
- `restart_lsp_server({ root_dir })` 会失败并把服务弄死：换 root 直接 `start_lsp`；卡死先 `pkill -f pyright-langserver` 再 `start_lsp`。
- 改状态的调用串行（`open_document`、`close_document`、`rename_symbol`、`refactor`、`safe_apply_edit`、`insert_*_symbol`、`replace_symbol_body`、`simulate_edit`），只读的并发。串行是调用次序，不是分轮；一轮内可以连续发多个编辑调用。

## 改与试

- `replace_symbol_body` 的 `new_body` 只给定义行之后的行，把 `def` 行一并写进去就会出现两行 `def`；`insert_after_symbol` 的 `code` 则要给完整的定义行。
- 多行参数的签名会被 `replace_symbol_body` 折断：改完文件开头只剩 `def name(`，报 `SyntaxError: '(' was never closed`。这类函数改用 `safe_edit` 整段替换，改完核签名行。
- `symbol_path` 走点号路径。Go 的方法在 outline 里写作 `(Circle).Area`，`replace_symbol_body` 两种写法都回 `symbol "Area" not found at current level`，此时回到 `safe_edit`。
- `safe_edit` 是「预览 + 应用」的一步版：净增量为 0 才落盘，否则回 `applied=false` 与预览诊断。
- `safe_edit` 只替换一段连续原文。同一文件有多处互不重叠的改动时，把每处区间放进一个 `WorkspaceEdit` 交给 `apply_edit`，一次落盘；拆成多次 `safe_edit` 是把一条编辑链拆成多次调用，不是串行。
- 改一个符号前先一次问清：`get_symbol_source` 取它的完整源码，`resource.read` 一次读到 import 段结束。签名跨行时按行列取，不拿 `position_pattern` 猜；改 import 前先确认那一行存在。
- `apply_edit` 与 `safe_edit` 只接受 LSP 根之下的路径：改另一个仓的文件先 `start_lsp` 指到那个根，或退回一次整文件读写。
- `safe_delete_symbol` 尚被引用时回 `symbol has N references; cannot safely delete`。
- 改名或删除前先问边：`explore_symbol`、`blast_radius` 在改之前跑。符号一删，`find_references` 再没有提问对象；删完才枚举，只剩跑测试与逐行读文件。
- 改名先 `find_references` 看调用面，再 `rename_symbol({ dry_run: true })` 看落点；去掉 dry_run 直接改盘，故先保证工作树干净。
- 模拟会话链 `NetDelta=0` 只证明服务没推新诊断：gopls 推编译器错误，pyright 不推。Python 上 `preview_edit` / `safe_edit` 通过不构成证据，仍以项目检查命令判。
- `simulate_edit` 的区间含首尾行，`new_text` 整段替换该区间；替换函数体只取定义行之后的行。
- `commit_session` 一返回就把会话置为 committed，`apply: false` 也一样；用完 `destroy_session` 释放。

## 按名接线的框架

按参数名接线的框架里，节点之间没有一次调用，LSP 认不出这条边：`find_references` 回 0 条并提示「may be dead code」，而这个名字就出现在下游节点的签名里。`blast_radius` / `explore_symbol` 回 `symbols=0` 且正文带 `indexed=true` 时，读作「这张图里没有调用边」，不是「没人用」。接线面问框架自己的图，不 grep。

## 诊断

`get_diagnostics` 只回服务器已推送者，空结果不代表文件干净。`run_build` 跑 PATH 上的 `mypy`，不读项目配置；`run_tests` 对 python 走 `pytest --tb=json`，本机不认该取值。取真错用项目自己的检查命令。

`find_references` 回 0 条且无 `indexed` 标记，不是「没有调用者」：消费者文件未入索引时同样回 0，类方法尤甚（实测五处调用回 0 条）。报出服务与文件，把这一层失败写进回答，再决定是否换路。`blast_radius` 回 `symbols=0` 也可能是它枚举不到导出符号，与「这张图没有调用边」不可区分（实测 `strategy/futures/daily.py` 之 `Daily`）：改签名前按单符号 `find_references` 逐文件枚举，逐条落实构造点，不按列位猜哪条是构造、哪条是标注。

`list_symbols` 超时不是退回 grep 加 read 的理由：报出服务与文件，换一个能索引它的服务。任何从 LSP 退到读文件或 grep 的动作，先说出缺的是哪一层；说不出即不换。
