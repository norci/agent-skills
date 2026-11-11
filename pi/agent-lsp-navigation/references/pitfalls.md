# 判据的由来

SKILL.md 只留形状与判据。这里是判据背后的原始观测：某个形状回了什么、某次调用报什么错。判据本身变了才回来改这里。

## 抢锚与跨类同名

- 同一文件里同时有 `load` 与 `load_all` 时，`'def load@@'` 回 `SymbolName=load_all`，行号是后者的定义行。
- 前缀式 `'@@def load'` 与收尾式 `'load@@'` 同效；TS 与 Python 上 `find_references` 各回同样条数。跨语言仍有差异，取源码与查引用优先收尾式。
- 签名片段作锚落在参数上：`'def load(path@@'` 回 `SymbolName=path`。
- 两个类各有 `fetch` 时，`'def fetch@@'` 回先出现者，`SymbolName=fetch`，自洽校验照样通过 —— 名字相等证明不了取对。
- 猜函数名会落空：不存在的名字报 `position: position_pattern not found in file: "def <name>@@"`。故先 `list_symbols({ file_path, format: 'outline' })` 看符号树。

## 卡死与复位

- 并发五条 `get_symbol_source` 后全部回 `get_symbol_source: request textDocument/documentSymbol timed out after 30s`。
- `pkill -f pyright-langserver` 后第一次 `start_lsp` 回 `MCP connection closed`，第二次回 `LSP server started successfully`。
- `detect_lsp_servers` 回 `InstalledServers [2]{ConfigEntry,Language,Path,Server}` 与 `NotInstalled=-`；缺二进制者列在 `NotInstalled`。
- 服务状态查 CLI：`agent-lsp daemon-status` 回 `python (/abs/project) — PID 1118299, ready, uptime 9m29s`。
- 索引竞态实测 329 ms 后可用。

## 三关的原始报错

- 路径关：相对路径按进程 cwd 解析，回 `file path "/abs/cwd/src/a.ts" is outside workspace root "/abs/project"` —— 看着像权限问题，其实是路径解析。
- 项目关：`find_symbol` 走 tsserver 的 navigateToItems，目录里没有 `tsconfig.json` / `jsconfig.json` 时回 `symbols=0`，正文带 `TypeScript Server Error (5.9.3) No Project`；有 tsconfig 的目录上同一查询回 `symbols=1`。
- 形态关：minified / bundle 文件 `list_symbols` 报 `request textDocument/documentSymbol timed out …`；判断依据是行数少而单行极长。
- `add_workspace_folder` 只收 `path`，写 `folder_path` 回 `must have required properties path`。
- `go_to_definition` 的 schema 列了 `position_pattern`，只给 pattern 却报 `must have required properties line, column`。
- `explore` 的 schema 把 `line` 标成可选，只给 `file_path` 报 `line: missing required argument "line"`。
- `restart_lsp_server({ root_dir })` 回 `failed to restart LSP server: start process: exec: no command`，此后所有工具不可用；再调 `start_lsp`（同一 root_dir）即复原。
- `line` 单独给 `get_symbol_source` 时返该行所属的整个符号：给一个方法所在行，实际回整个 `class`。

## 图式符号

按参数名接线的框架里，节点被另一节点按名取用，`find_references` 回 0 条并提示「may be dead code」；同一文件 `blast_radius` 也不列该符号。

实测：一个 Hamilton 图模块里 `blast_radius({ changed_files: ['…/<图模块>.py'] })` 回 `symbols=0`，而同一模块里下游节点的签名中就有被问节点的名字作参数名。同一文件上 `explore_symbol` 反倒回十条真实调用边 —— 全是测试函数直接调用它，测试走的是普通调用而非图接线。

## 每请求超时与慢工具

- pi 的 MCP 每请求超时缺省 60 秒，配置键是 `timeout`（秒），落在用户级 `mcp.json` 的 server 条目上；形参在工具 schema 里没有，调用方无法按次覆盖。
- `blast_radius` 单文件实测约 30 秒，与文件大小无关（130 行的模块也是这个量级）；一次给两个文件即撞上 60 秒缺省上限，回 `MCP request timed out after 60000ms`。同一并发批里 `explore_symbol` / `find_references` / `list_symbols` 均正常返回，慢的是 `blast_radius` 自己。
- 并发五条 `get_symbol_source` 会让 pyright 的 `textDocument/documentSymbol` 在 30 秒处超时（见「卡死与复位」），而单条串行正常 —— 慢工具与改状态调用都要串行。
- `preview_edit` 的 schema 只列 `file_path` 必填，实际先报 `workspace_root is required`、补后又报 `language is required`，两者补齐仍撞 60 秒上限回 `MCP request timed out after 60000ms`。判影响面改用 `safe_edit` 回的 `net_delta` 或模拟会话链。
- `blast_radius` 给三个文件回 `symbols=148 edges=262`，同一批里 `explore_symbol` / `find_references` 正常 —— 时间随文件数涨，不随单文件大小涨。

## 工作区外的文件

- `apply_edit` 传工作区外路径回 `file path "…" is outside workspace root "…"`；同一路径上 `safe_edit` 回 `Error: preview failed: create_session failed: no LSP client available — call start_lsp first` —— 看着像服务没起，其实是路径关。改技能、配置这类工作区外文件用普通写文件工具。
- `find_symbol` 只认裸名：`{ query: '类.方法' }` 回 `symbols=0`，`{ query: '类' }` 回同一族 24 条。找方法定义先用 `list_symbols` 取类，再在类里找。
- `get_cross_repo_references` 的参数是 `symbol_file` / `line` / `column` / `consumer_roots` / `language_id`，不是 `file_path` 加 `position_pattern`。
- `get_symbol_documentation` 只认该语言文档工具能解析的全名：第三方库的成员属性回 `No Python documentation found for '…'`，与「该符号没有文档」不可区分。

## 能力矩阵与模拟编辑

- `get_server_capabilities` 回 `Capabilities` / `Skills` / `SupportedTools` / `UnsupportedTools`。pyright 实测 `UnsupportedTools[3]: format_range,get_diagnostics,type_hierarchy`（gopls 已列出 `get_diagnostics` 却仍能回 `## [0]`，与清单不一致，按实测）；`go_to_implementation` / `get_inlay_hints` / `get_semantic_tokens` / `format_document` 在 pyright 上分别回 `Unhandled method textDocument/implementation` / `inlayHint` / `semanticTokens/full` / `formatting`。
- `type_hierarchy` 在 gopls 上回 `## targets @0 iface …Shape` 与 `edges: @0<@1 implements`（接口方向），对具体 struct 反向查 `supertypes` 回 `@1<@0 extends`。落在函数上回 `type_hierarchy (prepare): lsp error 0: not a type name`；pyright 上落在类定义回 `No type hierarchy item found`（`typeHierarchyProvider` 缺）。
- `find_callers` / `callers` 的位置要落在定义行的函数名标识符上：落在 `def` 关键字列回 `No call hierarchy item found`，落在函数体回同一句，落在接收者括号上回 `lsp error 0: c is not a function`。同一位置 `find_callers` 不带 direction 会多回 `typeshed-fallback/stdlib.sum` 一类被调者；`callers` 与 `find_callers({direction:'incoming'})` 输出逐字相同。
- `get_document_highlights` 在函数名上回 5 条含 `Kind=2`（读）的区间，用于文件内变量读写点；它不触发全库索引，比 `find_references` 快。
- `create_simulation_session` 回 `session_id=…\nstatus=created`；`simulate_edit` 回 `EditApplied=true\nVersionAfter=1`；`evaluate_session` 回 `NetDelta=0\nConfidence=high`；`commit_session({apply:false})` 回 `Patch` 键值，并把会话置为 committed，随后 `discard_session` 回 `already in terminal state: committed`。`simulate_chain` 回 `SafeToApplyThroughStep=2\n## Steps [2]{…}`。
- pyright 不推诊断：把 `return value + 1` 改为 `return undefined_name + 1` 与 `return value + "x"`，两次 `preview_edit` 都回 `NetDelta=0` 与 `Safe to apply`。gopls 推编译器错误：把 `s.Side * s.Side` 改为含 `s.undefinedThing`，回 `NetDelta=4` 与 `ErrorsIntroduced` 表（`undefined: s`、`declared and not used: sh`）。
- `simulate_edit` 的 `end_line` 含本行：区间写成 `24..25` 且 `new_text` 带 `def` 行，patch 里出现两行重复的 `def helper(value: int) -> int:`。
- `safe_delete_symbol` 对被引用者回 `symbol has 2 references; cannot safely delete`。
- `safe_edit` 与 `safe_apply_edit` 回同一形状：`applied=true\nnet_delta=0\nscope=file`。
- `start_lsp` 累加：同一进程内先起 python（/tmp/lspprobe）、再起 go（/tmp/goprobe）、再起 typescript（/tmp/tsprobe）后，`find_symbol({query:'total'})` 回 102 条，跨三个项目与 Go 标准库；`go_to_symbol({symbol_path:'total'})` 回的是 /tmp/tsprobe 里 `totalArea` 的定义，而非 Go 项目里的 `func total`。
- `go_to_symbol` 只认当前服务里存在的名字；`{symbol_path:'helper'}` 回 `no symbols found for symbol_path: helper`。
- Go 的方法在 outline 里是 `(Circle).Area`；`replace_symbol_body` / `safe_delete_symbol` 用 `Circle.Area` 与 `(Circle).Area` 都回 `symbol "Area" not found at current level`。
- `blast_radius` 的 `scope:'all'` + `include_transitive:true` 在 Go 文件上回 11 个节点与 `@4<@9 calls` 的二阶边；同一调用在服务刚起、索引未完成时回 `symbols=0`，重起或等待后恢复正常。
- `run_tests` 对 python 走 `pytest --tb=json`，回 `argument --tb: invalid choice: 'json'`。`run_build({workspace_dir})` 回 `unsupported language:`（空语言）。
- `refactor` 不带 action：gopls 回 `{"title":"Extract declarations to new file","kind":"refactor.extract.toNewFile"}`，tsserver 回 `{"title":"Move to a new file","kind":"refactor.move.newFile"}`；带不符的标题回 `no refactoring matches "…" here`。
- `get_completions` 在 TS 上回 `Items [983]`，输出被截断到 14307 token。
- `get_symbol_documentation({symbol:'strings.Split', language_id:'go'})` 回 `Source=toolchain` 与完整 doc；`{symbol:'fmt.Println'}` 回 `Error="doc: symbol fmt is not a type in package main…"` —— 只认类型与函数全名，包名本身不算。
- `get_inlay_hints` 在 gopls 与 tsserver 上都回空（`=-` / `## [0]`），不能据此判断类型推断不可见。
- `activate_skill({ skill_name })` 回 `{"allowed_tools":[…],"current_phase":"…","forbidden_tools":[…],"mode":"warn","status":"activated","total_phases":N}`，紧接着 `get_skill_phase` 回同一 `current_phase`，两者一致；`deactivate_skill` 回 `{"status":"deactivated"}`。更早一次观测里两者不一致（`activate_skill` 说已激活、`get_skill_phase` 说 `active:false`），该次之后未再复现。`mode=warn` 表示只提示，不拦调用。
