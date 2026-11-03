---
name: hermes-ops
description: 凡操作 Hermes 本体（CLI、配置、TUI、卸载、技能归属判定、web 后端、审批超时、后台任务）时，即当加载。
---

# Hermes 本体运维

## 查错起点

- 首检 `~/.hermes/logs/` 或 `hermes logs` 的会话存档以溯其源。
- 速辨常见错：apt/dpkg 锁、SSL 错、镜像源路径、权限问题。
- 先排除己误，不推诿用户。

## skill 归属判定

不可凭目录结构或文件存在性推测某 skill 是否为 bundled。Hermes 以 `~/.hermes/skills/.bundled_manifest`（`name:hash` 格式）为权威判定源，源码中 `tools/skill_usage.py::_read_bundled_manifest_names()` 负责读取。`hermes update` 输出的 `Syncing bundled skills... ~ N user-modified (kept)` 即依据此 manifest。从 Lisp 等脚本判断时直接读该文件，无需遍历目录比对。

Hub 安装者见 `~/.hermes/skills/.hub/lock.json` 的 `installed` 字段；`consolidated/` 类为 curator 合并产物。

## web 后端陷阱

`web_extract` 依赖 `web.extract_backend` 配置。若后端为 SearXNG（默认），则它只是搜索后端、无抓取能力，调用返回 `SearXNG is a search-only backend and cannot extract URL content`。此时改用：① `curl` 或 `w3m -dump` 取 HTML，再以 `BeautifulSoup` + `markdownify` 转 Markdown；② `browser_navigate` + `browser_snapshot full=true`。欲用本机 CRW 作抓取服务，按 Firecrawl 兼容后端接入，见 `references/crw-firecrawl-hermes.md`。

## 搜索受阻时

`web_search` 返回无关结果、`browser` 无法导航、`curl` 返 403/404 时，勿反复换同义词。停步评估：是否有现成资源（用户已下载、本地已有、他路可获）？若无，直告当前网络限制。

## 后台任务

以 `notify_on_complete=true` 运行，事毕自报。服务启动后以健康检查或日志信号验证就绪，再行后续操作。

## 功能卸载

- **先辨源码与产物**：`src/`、`ui-tui/src/`、`hermes-agent/**/*.py` 属源码，不可擅删；`node_modules/`、`dist/`、`build/`、`venv/` 属产物，可清。
- **TUI 卸载安全路径**：`ui-tui/` 的 `node_modules/` 与 `dist/` 可整目录删除，核心 agent（`venv/bin/hermes`）不受影响；删后 `hermes --version`、`hermes status` 应正常。
- **问清范围再动手**：只说「卸载」而未指明范围时，默认只清构建产物。

## TUI 剪贴板

Hermes TUI 基于 Ink（React for CLI），跑在终端 raw mode：Ctrl+C 被截获为 SIGINT，终端模拟器无法原生复制。变通：① 终端层叠加高亮（部分终端可 bypass raw mode 选中）；② 退出后从 `~/.hermes/logs/` 或 `hermes logs` 取回；③ 长文用 `hermes chat` 或 `hermes -z`，沿用终端原生复制。根治须在 `ui-tui/src` 全局快捷键监听处拦截 Ctrl+C 并调 `clipboard.writeText()`，属代码级改动。

## 超时

`approvals.timeout` 管危险命令审批超时，`clarify.timeout` 管 agent 向用户发问的等待超时，两者不可混用。长时间无人值守时调前者。

## memory remove

`memory(action='remove')` 的 `old_text` 是全文匹配，非子串或模糊匹配。从系统提示或会话中看到片段时不可直接用于 remove，须先 `memory(action='list')` 取完整条目文本。

## 技能合并

遇两 skill 内容重叠：**辨**（列重叠与差异）→ **定**（详备者为主文）→ **削**（删主文冗余，辅文改一行援引）→ **泛**（具体人名、路径换泛指，毋留会话之痕）→ **验**（自问是否尚有重复、援引是否清晰）。
