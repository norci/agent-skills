# LSP 服务 — 装什么、怎么装、怎么验

agent-lsp 只做 MCP 转发，真干活的二进制须在 PATH 上。本机已装（2026-11 实测）：python 走 `pyright-langserver`、go 走 `gopls`、rust 走 `rust-analyzer`、typescript 走 `typescript-language-server`、json 走 `vscode-json-language-server`，`mypy` 供 `run_build`。

## 先看缺什么

```ts
detect_lsp_servers({ workspace_dir: '/abs/project' });
```

回 `InstalledServers`（`"python:pyright-langserver,--stdio"|python|/path|server` 逐行）、`NotInstalled`、`SuggestedConfig`。`NotInstalled` 里的即缺，按下表装。

## 安装

| 语言 | 命令 | 落到 |
| --- | --- | --- |
| python | `bun add -g pyright` | `~/.bun/bin/pyright-langserver` |
| python 检查器（供 `run_build`） | `uv tool install mypy` | `~/.local/bin/mypy` |
| typescript | `bun add -g typescript@5 typescript-language-server` | `~/.bun/bin/typescript-language-server` |
| json / css / html | `bun add -g vscode-langservers-extracted` | `~/.bun/bin/vscode-json-language-server` 等三个 |
| go | `go install golang.org/x/tools/gopls@latest` | `~/go/bin/gopls` |
| rust | `rustup component add rust-analyzer` | `~/.rustup/toolchains/*/bin/rust-analyzer` |

装完 `command -v <binary>` 确认 PATH 可见；`~/.local/bin` 与 `~/go/bin` 需在 PATH 内。

## 验

```ts
start_lsp({ root_dir: '/abs/project', language_id: 'python' });
// -> LSP server started successfully
```

再跑一次 `detect_lsp_servers`，装上的语言应进 `InstalledServers`。

## 坑

- **`language_id` 指名缺二进制的语言即整体失败**：`start_lsp({language_id:'rust'})` 在组件未装时回 `lsp process exited: exit status 1; server stderr: error: Unknown binary 'rust-analyzer' in official toolchain`。此时改不带 `language_id` 起其余已装者，或先装组件。
- **`json` 不能指名**：`detect_lsp_servers` 已列 `json:vscode-json-language-server,--stdio`，但 `start_lsp({language_id:'json'})` 回 `no server configured for language "json"`；不带 `language_id` 起全部时 json 一并起得来。
- **`run_build` 不读项目配置**：python 分支直接调 PATH 上的 `mypy`（未装时报 `executable file not found in $PATH`），不看 `pyproject.toml` 之 mypy 段，故只在装了该二进制时可用；项目自己的检查命令仍是首选。
- **`rust-analyzer` 的 `/usr/bin` shim 不算装好**：rustup 的 shim 在组件缺失时照样存在于 PATH，报错在起服务时。
