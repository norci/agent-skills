---
name: agent-lsp-navigation
slug: agent-lsp-navigation
description: 用 agent-lsp 的 MCP 工具做符号定位、引用查找、类型错诊断、改名与重构。凡需在 go/typescript/python/rust 项目里跳转定义、看调用方、查诊断、改符号时用。
---

# agent-lsp

MCP 服务 `agent-lsp`（0.24.2）在 pi 里捕获成 `extensions.mcp__agent_lsp__<tool>`，**下划线**。外部文档与 skills.sh 上的 skill 写的是 `mcp__agent-lsp__`（连字符），照抄调不到。

参数名一律用 `tools.describe({ ref: 'extensions.mcp__agent_lsp__<tool>' })` 取，不猜。下表是实测过的必填项。

| 任务 | 工具 | 必填参数 |
|---|---|---|
| 起服务 | `start_lsp` | `root_dir`（含 package.json / go.mod 的目录）+ **`language_id`** |
| 查类型错 | `get_diagnostics` | `file_path`（绝对路径） |
| 按名找符号 | `find_symbol` | `query` |
| 文件里有什么 | `list_symbols` | `file_path` |
| 看符号源码 | `get_symbol_source` | `file_path` + `line` |
| 谁引用了它 | `find_references` | `file_path` + `line`/`column`（或 `position_pattern`） |
| 符号类型详情 | `inspect_symbol` | `file_path` + `line`/`column`（或 `position_pattern`） |
| 打开文档 | `open_document` | `file_path` |
| 编译 | `run_build` | `workspace_dir` |
| 跑测试 | `run_tests` | `workspace_dir` |
| 探测可用语言服务器 | `detect_lsp_servers` | `workspace_dir` |

不存在 `relative_path`、`name_path_pattern`、`workspace_dir`（除上表三处）、`symbol` 这些参数——那是 serena 的口径，传了报 `schema is false`。

## 握手

多服务器模式下 `start_lsp` 不带 `language_id` 会依次初始化所有已配置服务器，任一失败即整体失败（本机 rust-analyzer 未装，报 `Unknown binary 'rust-analyzer'`）。**必带 `language_id`。**

```ts
await extensions.mcp__agent_lsp__start_lsp({ root_dir: '/abs/project', language_id: 'typescript' });
// -> "LSP server started successfully"
```

`language_id` 取值：`go`、`typescript`、`javascript`、`python`、`rust`。

## 常用调用

```ts
// 按名搜（全库）：返回 targets 列表，indexed=true 表示索引就绪
await extensions.mcp__agent_lsp__find_symbol({ query: 'add' });
// -> @0 fn lspcheck/src.add 1.00 lsp_resolved

// 单文件符号表
await extensions.mcp__agent_lsp__list_symbols({ file_path: '/abs/src/a.ts' });

// 取某行的符号源码
await extensions.mcp__agent_lsp__get_symbol_source({ file_path: '/abs/src/a.ts', line: 1 });
// -> SymbolName=add / StartLine=1 / EndLine=1 / Source="export function add(...) {...}"
```

## 坑

- TypeScript 项目的 workspace 里必须有带 `tsserver.js` 的 `typescript@5`；`typescript@7` 报 `provides no tsserver.js`，没有 typescript 报 `Could not find a valid TypeScript installation`。`bun add typescript@5` 即可。
- `get_diagnostics` 常回 `No diagnostics received — the server has not published any for this document`，即使文件有类型错。先 `open_document` 再等 2–4 秒重取；仍为空时改用 `run_build` 或 serena 的 `get_diagnostics_for_file`，不要把空结果当「文件干净」。
- 未起服务就调其余工具，一律回 `LSP client not initialized; call start_lsp first`。
- 工作目录换了要重新 `start_lsp`，`root_dir` 按新项目根给。

## 相位护栏

服务端内置 24 个 workflow skill，正文不在本地，但相位约束可开：

```ts
await extensions.mcp__agent_lsp__activate_skill({ skill_name: 'lsp-verify', mode: 'warn' });
// -> {status:'activated', current_phase:'test_correlation', total_phases:5, allowed_tools:[...], forbidden_tools:[...]}
await extensions.mcp__agent_lsp__deactivate_skill({});
```

`skill_name` 例：`lsp-rename`、`lsp-refactor`、`lsp-safe-edit`、`lsp-verify`。`mode` 取 `warn`（默认，记日志放行）或 `block`（越序报错）。
