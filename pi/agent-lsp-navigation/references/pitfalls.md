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

按参数名接线的框架里，节点被另一节点按名取用，`find_references` 回 0 条并提示「may be dead code」；同一文件 `blast_radius` 也不列该符号。消费者以 grep 参数名为准。
