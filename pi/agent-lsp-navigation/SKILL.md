---
name: agent-lsp-navigation
description: LSP 符号导航——按符号取源码、查调用者与类型层级、算影响面、模拟编辑的工具形状与返回信封。凡要读、找、改 .py/.ts/.go/.rs 源码，动手之前先读本技能；先 grep 或先整文件 read 即属绕行。
---

# agent-lsp

判据背后的原始观测（某文件某行回什么、某次调用报什么错）在 `references/pitfalls.md`，服务安装与能力差异在 `references/servers.md`，怀疑判据时才读。

## 工具全表 — 只调取源码，其余分析就全靠手工

agent-lsp 暴露的工具远不止取源码与符号树。只调那两件，调用关系、影响面、改名落点、试改诊断都得手工拼，而它们各有现成的一次调用。下表按用途分组，名字即入口。

| 用途 | 工具 |
| --- | --- |
| 读 | `list_symbols`、`get_symbol_source`、`inspect_symbol`、`find_symbol`、`go_to_symbol`、`get_symbol_documentation` |
| 关系 | `explore_symbol`（`explore` 同义）、`callers`、`find_callers`、`find_references`、`get_document_highlights`、`type_hierarchy`、`go_to_implementation`、`go_to_definition`、`go_to_declaration`、`go_to_type_definition`、`get_cross_repo_references` |
| 影响面 | `blast_radius`、`detect_changes`、`get_tests_for_file` |
| 改 | `safe_edit`（`safe_apply_edit` 同义）、`apply_edit`、`replace_symbol_body`、`insert_before_symbol`、`insert_after_symbol`、`safe_delete_symbol`、`rename_symbol`、`refactor`、`suggest_fixes`、`execute_command` |
| 试与验 | `create_simulation_session`、`simulate_edit`、`simulate_chain`、`evaluate_session`、`commit_session`、`discard_session`、`destroy_session`、`preview_edit`、`get_diagnostics`、`get_completions`、`format_document`、`format_range`、`get_inlay_hints`、`get_semantic_tokens` |
| 会话 | `start_lsp`、`restart_lsp_server`、`detect_lsp_servers`、`open_document`、`close_document`、`add_workspace_folder`、`list_workspace_folders`、`remove_workspace_folder`、`set_log_level`、`get_server_capabilities`、`get_skill_phase`、`activate_skill`、`deactivate_skill`、`did_change_watched_files`、`import_cache`、`export_cache`、`run_build`、`run_tests` |

判据：本轮手工做的每一步，先在这张表里找一件能答它的工具；找得到而不用，那一步就是绕行。

## 一问一调用

能从上表答出的问题，不许 grep，不许整文件 read。表里的「一次调用」是这一问的唯一入口；手工做的那一步若在上表能找到一件能答它的工具，那一步就是绕行。

| 问什么 | 一次调用 | 回什么 |
| --- | --- | --- |
| 这个符号是什么、谁用它、有没有测试 | `explore_symbol` | 签名 + 源码 + 调用者 + 引用 + 测试者，一张图；测试者按真实调用边算 |
| 改这几个文件会牵连谁 | `blast_radius` | 按 test / non-test 分区的调用者，边带 lsp_resolved |
| 谁调这个函数 | `callers({ direction: 'incoming' })` | 调用者图 |
| 这个函数调了谁 | `callers({ direction: 'outgoing' })` | 被调者图 |
| 类与接口的父子关系 | `type_hierarchy` | extends / implements 边 |
| 接口或抽象方法有哪些实现 | `go_to_implementation` | 实现位置清单 |
| 文件里有什么 | `list_symbols({ format: 'outline' })` | 符号树，含方法、字段与行号 |
| 一个符号的源码 | `get_symbol_source` | `StartLine` / `EndLine` / `Source` |
| 这个函数收什么参数 | `inspect_symbol` | 签名与文档，不必打开被调者文件；`get_signature_help` 在 pyright 上回 `null` |
| 标准库或依赖里某符号的文档 | `get_symbol_documentation` | 工具链原文（`go doc` / `pydoc`），不读 vendor；只认该工具能解析的全名，第三方库的成员属性多回「没有文档」 |
| 本文件里这个变量在哪读、在哪写 | `get_document_highlights` | 该符号在全文件的所有读写点（不止指针所在那一个），`Kind` 2=读、3=写 |
| 这段改动会不会坏 | `safe_edit` 回的 `net_delta`、或模拟会话链 | 诊断增量（只在服务推诊断时可信，见下）；`preview_edit` 慢，见 pitfalls |
| 这个位置服务能做什么重构 | `refactor`（不带 `action`） | 该位置的可用重构清单 |
| 按名字改代码 | `replace_symbol_body` / `insert_before_symbol` / `insert_after_symbol` | 定位靠符号树，不靠行号 |
| 改名 | `rename_symbol({ dry_run: true })` | 逐文件的替换区间 |
| 提交前看未提交改动的影响 | `detect_changes` | 按 high / medium / low 分级的受影响符号 |
| 同包有哪些测试文件 | `get_tests_for_file` | 按目录约定列同包测试，不按导入关系；问「谁测了这个符号」用 `explore_symbol` |
| 跨仓谁用了这个符号 | `get_cross_repo_references` | 按仓库分区的引用边 |
| 按名字找定义，不知在哪个文件 | `find_symbol` | 定义位置；只认裸名，`类.方法` 回 0 条 |
| 跳到声明处、变量或表达式的类型定义 | `go_to_declaration` / `go_to_type_definition` | 行列区间 |
| 这个位置服务能给什么快速修复 | `suggest_fixes` | 修复清单；空表读作「该区间没有诊断」，不读作「没有修复」 |
| 不落盘试改一段会引入什么错 | 模拟会话链（见下节） | 诊断增量与 patch |
| 服务支持哪些工具、缺哪些 | `get_server_capabilities` | `SupportedTools` / `UnsupportedTools` |
| 这个位置有哪些候选名 | `get_completions` | 候选清单；只在窄位置用，宽位置回几百条 |

## 一轮开发的顺序

读、找、改各有其工具，按此序走，不退回 grep 与整文件 read：

| 步 | 调用 | 不做什么 |
| --- | --- | --- |
| 定位 | `list_symbols({ format: 'outline' })` 取符号树，再按符号树里的名字写锚 | 不猜函数名，不用 grep 找定义 |
| 读懂 | `get_symbol_source` 取整段原文；签名与文档用 `inspect_symbol` | 不整文件 read；不为「了解调用面」取原文（见下节） |
| 查牵连 | `blast_radius({ changed_files })`；`explore_symbol` 看谁在用、谁在测 | 不逐文件搜调用者 |
| 试改 | 模拟会话链，或 `safe_edit` 回的 `net_delta` | 不先落盘再靠跑测试发现语法错 |
| 改 | `replace_symbol_body` / `insert_before_symbol` / `insert_after_symbol` / `safe_edit` / `rename_symbol` | 不按行号改，不 sed |
| 验 | 项目自己的检查命令 | 不把 `get_diagnostics` 的空结果当干净 |

新写一个文件时它还没有符号可锚，先用 `pi.write` 落全文；此后这个文件一律按符号改。

`blast_radius` 与 `detect_changes` 都不计未跟踪的新文件，故新文件的影响面须手动指名其路径再问一次。

## 调用关系问图，不问原文

「谁调用它、谁测它、改这里会牵连谁」由 `explore_symbol` 与 `blast_radius` 的 `## edges` 直接答出，读图即得。逐条 `get_symbol_source` 再把调用关系在脑子里拼出来是绕行：那是换了个入口读文件，而 LSP 早把这张图算好了。

判据：本轮取原文的次数等于本轮真正要改的符号数。多取的那些就是手工分析 —— 为「看看它被谁用」而取的原文，一段都不该有。

需要原文的只有两个问题：这段逻辑怎么写的、要改的是哪几行。取原文一次只取一个符号，取完就改，不攒着一起读。

取原文的理由写不出来时（例如「先看看整体」「了解一下上下文」），那就是在手工分析，停手改问图。

## 先问服务会什么

```ts
await extensions.mcp__agent_lsp__get_server_capabilities({});
```

回每个已起服务的 `Capabilities`、`SupportedTools`、`UnsupportedTools` 与 `Skills`。判据：不在 `SupportedTools` 里的工具不调，它的空结果也不当证据。pyright 实测缺 `type_hierarchy` / `format_range` / `format_document` / `get_inlay_hints` / `go_to_implementation` / `get_semantic_tokens`；gopls 与 tsserver 给的更全。

另一组接口按技能阶段约束可调的工具：`activate_skill({ skill_name })` 回 `current_phase` / `allowed_tools` / `forbidden_tools`，`get_skill_phase` 查当前阶段，`deactivate_skill` 退出。它只做提示（`mode=warn`），不替代项目自己的检查命令。

## 调用形状

工具名 `extensions.mcp__agent_lsp__<tool>`（**下划线**；外部文档写的 `mcp__agent-lsp__` 在 pi 里调不到）。逐次写全名：

```ts
await extensions.mcp__agent_lsp__find_references({ file_path, position_pattern: 'def available@@' });
```

**不要起中间别名**：`const L = extensions.mcp__agent_lsp__` 拿到的东西不可调用，`L.find_references` 报 `TypeError: not a function`。要动态取名就整串拼：

```ts
const lsp = (name: string, args: unknown) => (extensions as any)[`mcp__agent_lsp__${name}`](args);
```

参数以 `tools.describe({ ref: 'extensions.mcp__agent_lsp__<tool>' })` 为准 —— 它回 `inputSchema.properties`，是「这个工具收不收 `position_pattern`」的唯一权威答案。schema 列了而实测不收者，按实测（见 pitfalls）。

## 返回值

**先读这一节再写任何解析代码。** 每个工具回 MCP 信封，正文在 `.text`；`String(result)` 得 `"[object Object]"`。

```ts
const result = await extensions.mcp__agent_lsp__get_symbol_source({ file_path, position_pattern });
const text = String(result.text);
const start = Number((text.match(/StartLine=(\d+)/) ?? [])[1]);
const source = (text.match(/Source="((?:[^"\\]|\\.)*)"/) ?? [])[1] ?? '';
```

两类正文，靠首行区分：

- **`GCF profile=generic`** —— 键值块（`StartLine=96`），或 `## [N]{列名}` 表格（首列是行号）。表格的 `N` 即条数，不必数行。
- **`GCF profile=graph`** —— `## targets` / `## related` / `## edges`。`@k fn pkg.name 1.00 lsp_resolved` 一行一个节点，`@1<@2 calls` 读作「@2 调用 @1」。首行带 `symbols=N edges=M`，据此决定要不要细看。带 `lsp_resolved` 的边是语言服务器解析出来的，其余为推断。

- **符号字段只在正文里，不在信封的其它键上**：`.details` 只有 `{ server, tool }` 两键，写 `details.start_line` 得 `undefined` 且不报错，判据静默落空。
- `get_symbol_source` 回 `EndLine` / `Source` / `StartLine` / `SymbolKind` / `SymbolName` 的键值块；`Source` 里是带转义的整段源码（换行是 `\n` 两个字符），直接当文本读。
- `list_symbols` 与 `get_symbol_source` 的正文尾带 `{"_meta":{"token_savings":…}}`，那是省下的 token 数，不是内容。

### `StartLine` 落在装饰器行还是 `def` 行

装饰器属于定义，故带装饰器者指最外层装饰器行，不带者指 `def` / `class` / `async def` 行。定义行 = `StartLine` 加 `Source` 里首个 `def` / `class` / `async def` 行的下标；装饰器可跨多行（`@parameterize(` 之参数换行），不能用「固定加一」。写进文档的行号取定义行。

## 不回读原文复核 LSP 的结论

LSP 回的 `Source` 就是该符号在文件里的整段原文，`StartLine` / `EndLine` 就是它的行区间。定义行、签名、引用落在哪一行都能从这一次返回里算出来；再 `read` 核对等于把「查符号」降格成「读文件」。只有 LSP 不给的片段（非符号区域、被截断的长文件）才 `read`。

自洽校验就地做完：`Source` 里首个定义行的名字与 `position_pattern` 所指名字相同；`Source` 的行数等于 `EndLine - StartLine + 1`。怀疑公式失效时重发一次 `get_symbol_source`，不回读文件。

## 位置怎么给

**收 `position_pattern` 的**：`find_references`、`inspect_symbol`、`get_symbol_source`、`rename_symbol`、`explore`、`explore_symbol`、`refactor`。

**只收 `line` + `column`（1 起算）的**：`callers`、`find_callers`、`go_to_declaration`、`go_to_implementation`、`go_to_type_definition`、`go_to_definition`、`type_hierarchy`、`prepare_rename`、`suggest_fixes`、`get_document_highlights`、`get_signature_help`、`get_completions`。

`position_pattern` 把源码里的一行作锚，**以 `@@` 收尾**：

- 带不带 `def` 都行；前缀式 `'@@def _push'` 与收尾式 `'_push@@'` 同效，取源码与查引用优先收尾式。
- **先 `list_symbols({ file_path, format: 'outline' })` 看符号树，再选锚**，不猜函数名。猜出来的名字报 `position_pattern not found in file`。
- **同前缀者会抢锚**：文件里同时有 `load` 与 `load_all` 时，`'def load@@'` 回 `load_all`。故每次取源码先读正文的 `SymbolName=`，与所问名字不等即换锚。
- **同名跨类时 `SymbolName` 也不能证明身份**：两个类各有 `fetch` 时，`'def fetch@@'` 回先出现者。判身份靠 `list_symbols` 的类树，或锚取该类内一行独有原文（函数体一句 docstring）。
- 签名片段作锚会落到参数上：`'def load(path@@'` 回 `SymbolName=path`。

**line/col 必须落在标识符本身，且落在定义行**：

- 落在 `def` 关键字那一列、函数体、注释、接收者括号上，都不抛错，只回一句 `No call hierarchy item found at <path>:<line>:<col>` 或 `lsp error 0: identifier not found`。判成败看正文。Python 取名字首字母所在列，Go 取函数名标识符所在列。
- `type_hierarchy` 只认类型名；落在函数上回 `lsp error 0: not a type name`。
- 列越界回 `column is beyond end of line`，行越界回 `line number out of range 0-N`。
- **行号随编辑移动**：改过文件后先前记下的 line 作废，重取 `list_symbols` 或改用 pattern 锚。

## 握手

```ts
await extensions.mcp__agent_lsp__start_lsp({ root_dir: '/abs/project', language_id: 'python' });
```

- `language_id` 指名一门（`python` / `go` / `rust` / `typescript`）；不带则起已配置的全部。指名者缺二进制即整体失败，故先 `detect_lsp_servers({ workspace_dir })` 看 `InstalledServers` / `NotInstalled`。
- **`start_lsp` 是累加，不是替换**：换 root 再调一次，旧服务仍挂在 `AllServers` 里。故 `find_symbol` / `go_to_symbol` 会扇出到全部服务，把别的项目的同名符号混进结果（实测 `go_to_symbol({ symbol_path: 'total' })` 回的是另一项目里名字相近的符号）。**找定义优先 `list_symbols` + `get_symbol_source`，少用 `find_symbol` / `go_to_symbol`。**
- 未起时其余工具一律回 `LSP client not initialized; call start_lsp first`。
- 刚起服务时 `find_references` / `blast_radius` 可能回 `workspace is still being indexed by the daemon (started Ns ago)`，等 1 秒重试即可。`find_symbol` / `list_symbols` / `inspect_symbol` / `get_symbol_source` 不等索引。`start_lsp({ ready_timeout_seconds })` 可阻塞到索引完成。
- `restart_lsp_server({ root_dir })` 会失败并把服务弄死。换 root 直接 `start_lsp`，不要先 restart。卡死复位：`pkill -f pyright-langserver` 再 `start_lsp`。
- **改状态的调用须串行，只读的并发**：改状态者 `open_document` / `close_document` / `rename_symbol` / `refactor` / `safe_apply_edit` / `insert_before_symbol` / `replace_symbol_body` / `simulate_edit`；只读者 `get_diagnostics` / `list_symbols` / `get_symbol_source` / `find_references` / `inspect_symbol` / `callers` / `type_hierarchy`，一律 `Promise.all`。并发打十几条改状态调用会把它卡死。
- 路径必须绝对且落在已注册工作区内：相对路径按进程 cwd（在 pi 里是 `~/.pi`）解析，回 `is outside workspace root`。注册工作区用 `start_lsp({ root_dir })` 或 `add_workspace_folder({ path })`（只收 `path`）。

## 调用层级与类型关系

| 工具 | 收 | 回 |
| --- | --- | --- |
| `callers` | line/col + `direction` | 调用者图；`callers` 是 `find_callers` 的 incoming 快捷方式，实测两者同一张图 |
| `find_callers` | line/col + `direction` | 不带 direction 时被调者与相关符号一并回，噪声大，指明方向 |
| `type_hierarchy` | line/col + `direction` | `extends` / `implements` 边；`supertypes` 只向上，`subtypes` 只向下 |
| `go_to_implementation` | line/col | 接口或抽象方法的实现清单；pyright 不支持 |
| `go_to_type_definition` | line/col | 变量或表达式的类型声明，落在 stdlib 的 `.pyi` / 类型定义上 |
| `go_to_declaration` | line/col | 声明处，与 definition 同用的两条路 |
| `get_document_highlights` | line/col | 本文件内的读写点，`Kind` 2=读 3=写；查局部变量用它，不用 `find_references` |
| `explore_symbol` | pattern 或 line/col | 上述几项的合并版：签名 + 源码 + 调用者 + 引用计数 + 测试者 |

## 引用与影响面

| 工具 | 收 | 回 |
| --- | --- | --- |
| `find_references` | pattern 或 line/col；`include_declaration: true` 把定义行一并算 | 表头 `## [N]{EndCol,EndLine,FilePath,StartCol,StartLine}`，N 即条数 |
| `blast_radius` | `changed_files: ['/abs/a.py']` 文件数组（不是 `file_path`） | 按 test / non-test 分区；`filter: 'untested'` 只留「有生产调用者、无测试」者；`include_transitive` 加二阶；`scope: 'all'` 含未导出符号；**一次只给一个文件**，多文件一并问会撞 MCP 每请求超时；超时读作「没答」，不读作「没有调用者」 |
| `detect_changes` | `scope: 'unstaged' / 'staged' / 'committed'`，`range` 只对 committed 有效 | 自跑 `git diff` 再套 blast_radius，按 high / medium / low 分级；未跟踪的新文件不计 |
| `get_tests_for_file` | `file_path` | 该文件的测试文件清单（静态规则，不跑测试） |
| `get_cross_repo_references` | `symbol_file` + line/col + `consumer_roots` | 跨仓库引用，按 repo 分区；内部会加工作区并等索引 |

`find_symbol` 只认裸名：`LiveSession.on_tick` 回 0 条，`on_tick` 回全部同名者；无通配符；多服务并存时扇出到所有服务。重名多时用 `detail_level: 'hover'` 加 `limit` / `offset` 翻页。`find_symbol` / `go_to_symbol` 只在有 `tsconfig.json` 的 TS 项目根可用，否则回 `No Project`。

## 模拟编辑的判据只在一部分服务上成立

`create_simulation_session` → `simulate_edit`（逐条） → `evaluate_session` → `commit_session` → `destroy_session`，另有一条 `simulate_chain` 一次给多步并回 `SafeToApplyThroughStep`。

- `NetDelta=0` 只证明「服务没有推新诊断」，不证明改动正确。gopls 会推编译器错误（实测把函数体改成未定义变量，`NetDelta=4` 并列出 `undefined: s`）；pyright 不推（实测把 `return value + 1` 改成 `return undefined_name + 1`，仍回 `NetDelta=0` 与 `Safe to apply`）。故 Python 上的 `preview_edit` / `safe_edit` 通过不构成证据，仍以项目检查命令判。
- `simulate_edit` 的区间含首尾行，`new_text` 整段替换该区间。把 `def` 行也包进区间会写出重复的 `def` 行；替换函数体只取定义行之后的行。
- `commit_session` 一返回就把会话置为 committed，`apply: false` 只回 patch 也一样；此后 `discard_session` 回 `already in terminal state: committed`。用完 `destroy_session` 释放。

## 按符号改代码

- `replace_symbol_body` 的 `new_body` 只给定义行之后的行：把 `def` 行一并写进去，文件里就会出现两行 `def`。`insert_after_symbol` 的 `code` 则要给完整的 `def` 行，两者不同。
- `replace_symbol_body` / `insert_before_symbol` / `insert_after_symbol` / `safe_delete_symbol` 走 `symbol_path`（点号路径）。Python 的 `helper` 与 `Class.method` 可用；Go 的方法在 outline 里写作 `(Circle).Area`，`Circle.Area` 与 `(Circle).Area` 两种写法都回 `symbol "Area" not found at current level`，此时回到 `safe_edit` 按原文替换或按行区间 `apply_edit`。
- `safe_delete_symbol` 尚被引用时回 `symbol has N references; cannot safely delete`，不删；N 就是 `find_references` 的条数。
- `safe_edit({ file_path, old_text, new_text })` 是「预览 + 应用」的一步版：净增量为 0 才落盘，否则回 `applied=false` 与预览诊断。它与 `safe_apply_edit` 同义。

## 改名

- 先 `find_references` 看调用面，再 `rename_symbol({ dry_run: true })` 回 `workspace_edit` JSON（逐文件的替换区间）与 `preview.files` / `preview.locations`；看过落点再去掉 dry_run，此时**直接改盘**，故先保证工作树干净。不要把这个 edit 拆成 `apply_edit` 自己重放。
- `prepare_rename` 在 pyright 上回 `supported=false`，直接走 `rename_symbol({ dry_run: true })`。

## 图式符号：LSP 看不见按名接线的引用

按参数名接线的框架（如 Hamilton 的 driver）里，节点之间没有一次调用，故 LSP 认不出这条边：一个节点被另一节点的函数体按参数名取用，`find_references` 回 0 条并提示「may be dead code」。LSP 的「0 条」在此不代表死代码 —— 接线面问框架自己的图（见下）。

判据：`blast_radius` 与 `explore_symbol` 回 `symbols=0` / `edges=0` 且正文带 `indexed=true` 时，这是「这张图里没有调用边」，不是「没人用」。判据是「这个名字出现在别人的签名里，而不是出现在调用里」。

**接线面问框架自己的图，不 grep。** 框架把这张图算好了，grep 参数名是在纸上重算一遍，还漏掉跨模块、跨装饰器、条件接线。

| 问什么 | 一次调用 | 回什么 |
| --- | --- | --- |
| 谁在这个节点上游 / 下游 | `driver.what_is_upstream_of(name)` / `what_is_downstream_of(name)` | 节点对象清单；结果含所问节点本身，规则输入（配置对象一类）也在其中 |
| 两节点之间隔着谁 | `driver.what_is_the_path_between(a, b)` | 同一张图的节点对象 |
| 图长什么样、要贴给人看 | `driver.display_all_functions(path, keep_dot=True)` | 落 DOT；`keep_dot=False` 只渲不存 |

- 图从 `driver.Builder().with_modules(module).build()` 出来的 Driver 上取；上面的查询不需要额外依赖，出图才要 `pip install "sf-hamilton[visualization]"`，缺包抛 `ModuleNotFoundError` 并自带安装提示，`dot` 二进制只管把 DOT 渲成 png/svg。
- 返回的是节点对象，不是字符串：`sorted(driver.what_is_upstream_of(x))` 抛 `TypeError: '<' not supported between instances of 'HamiltonNode'`，先取 `.name`。
- 一个工程常有多张图（行情一张、策略一张），节点只在自己那张图里可见；问错图回 `ValueError: Unknown nodes [x] requested. Check for typos?`，这不是拼错，是问错了图。
- 符号的定义与函数体仍按符号改，只有「谁接谁的线」问图。

## 诊断与检查命令

- `get_diagnostics({ file_path })` 只回服务器已推送者，空结果不代表文件干净（正文自带此句）。`group_by: 'symbol'` 按符号归并。取真错用项目自己的检查命令（`uv run pyright` / `bunx tsc --noEmit` / `go build`）。
- `run_build` 跑 PATH 上的 `mypy`，不读项目配置，且需一个能被识别的 workspace：实测给 `workspace_dir` 仍回 `unsupported language`。
- `run_tests` 对 python 走 `pytest --tb=json`，本机 pytest 不认该取值，回 `argument --tb: invalid choice: 'json'`；测试命令仍以项目自己的为准。
- `refactor` 不带 `action` 列出该位置可用重构（gopls 给「Extract declarations to new file」，tsserver 给「Move to a new file」）；`dry_run: true` 只回编辑不落盘。标题须与清单逐字相同，否则回 `no refactoring matches …`。
- `get_completions` 在 TS 上实测回 983 条并触发输出截断，只在窄位置用。

## 文件形态

minified / bundle 文件不能按符号读（`list_symbols` 直接 `timed out`），判断依据是行数少而单行极长；改用 `pi.grep` 定行号，再 `pi.read({ offset, limit })` 取区间。
