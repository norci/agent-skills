---
name: agent-lsp-navigation
description: 凡要读、找、改 .py/.ts/.go/.rs 源码，动手之前先读本技能。先 grep 或先整文件 read 即属绕行。
---

# agent-lsp

判据背后的原始观测（某文件某行回什么、某次调用报什么错）在 `references/pitfalls.md`，怀疑判据时才读。

## 工具对照

| 要什么 | 用 |
| --- | --- |
| 一个函数/类/方法的源码与签名 | `get_symbol_source` / `inspect_symbol` |
| 文件里有什么（含方法与字段） | `list_symbols({ format: 'outline' })` |
| 全库按名找符号 | `find_symbol` |
| 谁引用了这个符号 | `find_references` |
| 改这个文件会波及谁 | `blast_radius` |
| 跨目录/跨仓库查符号 | `add_workspace_folder({ path })` |
| 按点号全名跳到定义 | `go_to_symbol({ symbol_path })` |
| 这个文件有哪些测试 | `get_tests_for_file` |
| 改名的全部落点 | `rename_symbol({ dry_run: true })` |

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

- 正文首行是 `GCF profile=generic`，图式工具是 `GCF profile=graph tool=blast_radius symbols=48 edges=68` —— 符号数与边数在首行，据此决定要不要细看。
- **符号字段只在正文里，不在信封的其它键上**：`.details` 只有 `{ server, tool }` 两键，写 `details.start_line` 得 `undefined` 且不报错，判据静默落空。
- `get_symbol_source` 回 `EndLine=` / `Source="..."` / `StartLine=` / `SymbolKind=` / `SymbolName=` 的键值块；`Source` 里是带转义的整段源码（换行是 `\n` 两个字符），直接当文本读。

### `StartLine` 落在装饰器行还是 `def` 行

装饰器属于定义，故带装饰器者指最外层装饰器行，不带者指 `def` / `class` / `async def` 行。定义行 = `StartLine` 加 `Source` 里首个 `def` / `class` / `async def` 行的下标；装饰器可跨多行（`@parameterize(` 之参数换行），不能用「固定加一」。写进文档的行号取定义行。

## 不回读原文复核 LSP 的结论

LSP 回的 `Source` 就是该符号在文件里的整段原文，`StartLine` / `EndLine` 就是它的行区间。定义行、签名、引用落在哪一行都能从这一次返回里算出来；再 `read` 核对等于把「查符号」降格成「读文件」。只有 LSP 不给的片段（非符号区域、被截断的长文件）才 `read`。

自洽校验就地做完：`Source` 里首个定义行的名字与 `position_pattern` 所指名字相同；`Source` 的行数等于 `EndLine - StartLine + 1`。怀疑公式失效时重发一次 `get_symbol_source`，不回读文件。

## 位置怎么给

**收 `position_pattern` 的**：`find_references`、`inspect_symbol`、`get_symbol_source`、`rename_symbol`、`explore_symbol`。

**只收 `line` + `column`（1 起算）的**：`find_callers`、`go_to_declaration`、`go_to_implementation`、`type_hierarchy`、`prepare_rename`、`suggest_fixes`、`go_to_definition`。落点必须真在标识符上：落空行、注释行、`def` 行本身都不抛错，正文回一句 `No call hierarchy item found at <path>:<line>:<col>` —— 判成败看正文，不能靠 try/catch。

`position_pattern` 把源码里的一行作锚，**以 `@@` 收尾**：

- 带不带 `def` 都行；前缀式 `'@@def _push'` 与收尾式 `'_push@@'` 同效，取源码与查引用优先收尾式。
- **先 `list_symbols({ file_path, format: 'outline' })` 看符号树，再选锚**，不猜函数名。猜出来的名字报 `position_pattern not found in file`。
- **同前缀者会抢锚**：文件里同时有 `load` 与 `load_all` 时，`'def load@@'` 回 `load_all`。故每次取源码先读正文的 `SymbolName=`，与所问名字不等即换锚。
- **同名跨类时 `SymbolName` 也不能证明身份**：两个类各有 `fetch` 时，`'def fetch@@'` 回先出现者。判身份靠 `list_symbols` 的类树，或锚取该类内一行独有原文（函数体一句 docstring）。
- 签名片段作锚会落到参数上：`'def load(path@@'` 回 `SymbolName=path`。

## 握手

```ts
await extensions.mcp__agent_lsp__start_lsp({ root_dir: '/abs/project', language_id: 'python' });
```

- `language_id` 指名一门（`python` / `go` / `rust` / `typescript`）；不带则起已配置的全部。指名者缺二进制即整体失败，故先 `detect_lsp_servers({ workspace_dir })` 看 `InstalledServers` / `NotInstalled`。
- 换工作目录须重起；未起时其余工具一律回 `LSP client not initialized; call start_lsp first`。
- 刚起服务时 `find_references` / `blast_radius` 可能回 `workspace is still being indexed by the daemon (started Ns ago)`，等 1 秒重试即可。`find_symbol` / `list_symbols` / `inspect_symbol` / `get_symbol_source` 不等索引。
- `restart_lsp_server({ root_dir })` 会失败并把服务弄死。换 root 直接 `start_lsp`，不要先 restart。卡死复位：`pkill -f pyright-langserver` 再 `start_lsp`。
- **改状态的调用须串行，只读的并发**：改状态者 `open_document` / `close_document` / `rename_symbol` / `refactor` / `safe_apply_edit` / `insert_before_symbol`；只读者 `get_diagnostics` / `list_symbols` / `get_symbol_source` / `find_references` / `inspect_symbol`，一律 `Promise.all`。并发打十几条改状态调用会把它卡死。
- 路径必须绝对且落在已注册工作区内：相对路径按进程 cwd（在 pi 里是 `~/.pi`）解析，回 `is outside workspace root`。注册工作区用 `start_lsp({ root_dir })` 或 `add_workspace_folder({ path })`（只收 `path`）。

## 引用与影响面

| 工具 | 收 | 回 |
| --- | --- | --- |
| `find_references` | pattern 或 line/col；`include_declaration: true` 把定义行一并算 | 表头 `## [N]{EndCol,EndLine,FilePath,StartCol,StartLine}`，N 即条数，不必数行 |
| `find_callers` | 只 line/col；`direction: 'incoming'` | 图：targets / related / edges；不带 direction 时被调者与相关符号一并回 |
| `blast_radius` | `changed_files: ['/abs/a.py']` 文件数组（不是 `file_path`） | 按 test / non-test 分区；`filter: 'untested'` 只留「有生产调用者、无测试」者；`include_transitive` 加二阶；`scope: 'all'` 含未导出符号 |
| `get_tests_for_file` | `file_path` | 该文件的测试文件清单 |
| `explore_symbol` | pattern 或 line/col | 该符号 + 相关测试的小图 |

`find_symbol` 只认裸名：`LiveSession.on_tick` 回 0 条，`on_tick` 回全部同名者；无通配符。重名多时用 `detail_level: 'hover'` 加 `limit` / `offset` 翻页。`find_symbol` / `go_to_symbol` 只在有 `tsconfig.json` 的 TS 项目根可用，否则回 `No Project`。

## 图式符号：LSP 看不见按名接线的引用

按参数名接线的框架（如 Hamilton 的 driver）里，节点之间没有一次调用，故 LSP 认不出这条边：一个节点被另一节点的函数体按参数名取用，`find_references` 回 0 条并提示「may be dead code」。图内接线以 grep 参数名为准，LSP 的「0 条」在此不代表死代码。

## 改名与类型错

- 先 `find_references` 看调用面，再 `rename_symbol({ dry_run: true })` 回 `workspace_edit` JSON（逐文件的替换区间）；看过落点再去掉 dry_run，此时**直接改盘**，故先保证工作树干净。`prepare_rename` 在 pyright 上不可用。
- `get_diagnostics({ file_path })` 只回服务器已推送者，空结果不代表文件干净（正文自带此句）。取真错用项目自己的检查命令（`uv run pyright` / `bunx tsc --noEmit` / `go build`）。`run_build` 跑 PATH 上的 `mypy`，不读项目配置。

## 文件形态

minified / bundle 文件不能按符号读（`list_symbols` 直接 `timed out`），判断依据是行数少而单行极长；改用 `pi.grep` 定行号，再 `pi.read({ offset, limit })` 取区间。
