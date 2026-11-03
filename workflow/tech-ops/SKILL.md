---
name: tech-ops
description: 技术操作之行为规范。凡涉编码生成、系统维护、操作验证、技能管理，即当加载。
---

# 技术操作之律

## 生成之律

- **唯留必需**：只生成用户要求之代码，不额外添加功能、示例或辅助代码
- **注释之律**：注释唯解释「为什么」，不解释「是什么」
  留：解释设计决策、标注非直觉行为、警示陷阱、TODO/FIXME
  留：公有 API 之 docstring
  删：逐行注释、函数头参数说明、复述代码逻辑之注释
- **生成不述**：代码/文档生成后，对话中毋重述其内容，只指明文件路径
- **技术专名存原貌**：`systemd`、`aria2`、`pip` 等毋妄译
- **格式**：换行分明，结构清晰

## 工作流之律

- 先查后写，毋重复造轮
- **多项检查类任务不用问「先做哪个」**：凡安全审计、系统体检、多步排查等逐项检查任务，当以 `todo` 列出完整清单，逐项执行，不得将选项抛给用户择一。用户若问「有无异常」，答「有」或「无」后附详情，不再反问「下一步查哪个」
- **勿让用户在多项子任务中选择**：若子任务 A/B/C/D 均为达成同一目标之必要步骤，则全部执行，不逐项请示。若某子项因工具限制无法执行（如非 root 无法查看进程绑定），跳过并记录跳过原因，继续下一项
- **工具存在性先于调用**：凡涉 CLI 工具，必先以 `which <tool>` 或 `command -v <tool>` 确认其存在
- 若官方已有规划，当以 PR 助力，勿另起炉灶
- **迁改优先于重写**：凡需移动文件/目录，先尝试 `mv` 而非 `rm + write_file` 生成新副本。后者多一倍写操作，浪费 token
- **memory `remove` 须全文匹配**：`memory(action='remove')` 以 `old_text` 作为全文匹配，非子串/模糊匹配。若从系统提示或会话中看到条目片段，不可直接用于 remove，须先以 `memory(action='list')` 或查看 memory 注入内容获得完整条目文本

## 查错之律
- 首检 Hermes 会话存档以溯其源
- 速辨常见错：apt/dpkg 锁、SSL 错、镜像源路径、权限问题等
- 先排除己误，不推诿用户
- **查证为先**：凡涉文件位置、技能归属、目录结构，必先以工具实查
- **先查后改**：改配置前先查当前值；创建远程资源前先查已有状态
- **源码优先，不反复问用户**：凡遇归属判定（bundled vs 自建 vs hub-installed）、文件路径、系统行为等可编程验证之问题，须深入源码或权威文件查证，不因边界模糊而反复提问用户。Hermes 的 `~/.hermes/skills/.bundled_manifest`（`name:hash` 格式）为 bundled 判定权威源，源码中 `tools/skill_usage.py::_read_bundled_manifest_names()` 负责读取
- **bundled skill 判定以源码为准**：不可凭目录结构或文件存在性推测某 skill 是否为 bundled。Hermes 以 `~/.hermes/skills/.bundled_manifest`（`name:hash` 格式）为权威判定源，源码中 `tools/skill_usage.py::_read_bundled_manifest_names()` 负责读取此文件。`hermes update` 时的 `Syncing bundled skills... ~ N user-modified (kept)` 即依据此 manifest。若需从 Lisp 等脚本中判断，直接读该文件即可，无需遍历目录比对
- **不可擅改系统配置**：remote URL、环境变量、网络代理、SSH 配置等，须先请旨
- **rm 超时之患**：`rm -rf` 于特定路径下偶发超时。补救：以 `shutil.rmtree()` 替代
- **重量级代理/凭证/工具链假设须先验证**：凡涉及外部 API key、代理方案、依赖可用性（如 `httpx[socks]`、`socksio`、`pass show` 越权、`pip` 缺失）等，不应假定其存在；先以最小探测（`which`、读环境、`import` 测试）确认，再选择路径。若假设成立（具足），解阻塞并继续；若全部未具足，须直告用户阻塞点与修复动作
- **`pass show` 回归 stdout**：若 `pass show <entry>` 是某凭证之源，脚本须直接 capture stdout 读取完整值。若仅看到脱敏形式（如 `sk-34e...243e`），不可将其写入磁盘视为完整 key——脱敏版会导致接口 401，却让脚本在"看起来有 key"的路上越走越远。另，若用户已明确说"用 pass show 读 key"，须把 subprocess 调用作为主路径，`key.yaml` 仅作 optional fallback
- **用户说"不许改 X"即为硬边界**：若用户在对话中明确说"不要再动 fetch-proxy.py"、"stop modifying X"、"don't patch X"，后续即便出现故障修复机会，也不得再 patch 该文件。须先向用户汇报现状，待其重新授权才可继续。沉默地重写脚本属于越界
- **代理变量污染规避**：凡用 `httpx.AsyncClient` 且宿主环境可能设 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`（尤其是 SOCKS 类型），须在脚本顶层主动清掉这些变量，或传 `proxy=None`，避免因 `socksio` 缺失而直接 ImportError 崩溃

## 硬件/sysfs 操作之律

- **先 `ls` 后写，不凭文档编造文件名**：Linux sysfs 文件（`/sys/class/hwmon/`、`/sys/devices/platform/` 等）是内核驱动的运行时窗口，**不存在即不可用**。写脚本前，必先以 `ls <目录>/` 确认真实文件名。
  - 教训案例：`nct6775` 驱动并无 `pwmX_stop` 文件；该驱动中最低 PWM 由 `pwmX_floor` 控制，而 `pwmX_stop_time` 是停转延迟（毫秒），非 PWM 值。凭文档臆造 `pwmX_stop` 属严重错误。
  - 必须逐一确认：`pwmX_enable`（控制模式）、`pwmX_target_temp`、`pwmX_temp_tolerance`、`pwmX_start`、`pwmX_floor`、`pwmX_step_up/down_time`、`pwmX_stop_time` 等均存在后方可写入。
- **温度源先读标签**：写 `pwmX_temp_sel` 前，先 `cat temp[N]_label` 确认各传感器身份（CPUTIN、SYSTIN、AUXTIN 等），勿猜测索引含义。
- **写入前后对比**：写 sysfs 前先读各文件的当前值（`cat pwmX_enable pwmX_target_temp ...`），写入后再次读取验证生效，确认无权限报错。
- **写入内容须符合单位**：`target_temp` 以毫摄氏度（m°C）为单位（`45000` = 45°C），`temp_tolerance` 亦然（`2000` = ±2°C），`step_up/down_time` 以毫秒为单位。

## Python 网络脚本运行律

凡涉及网络访问之 Python 脚本，须满足：

- **精确代理声明**：创建 `httpx.Client` / `httpx.AsyncClient` 时，显式传 `proxy=None` 以阻断默认代理链路。禁绝“任凭 httpx 依系统环境变量决策”的不稳定路径，尤其在 MITM 或容器环境中全局 `ALL_PROXY` 指向 SOCKS 服务、而本机遇未装 `socksio` 的情形下。若全局 `httpx.URL` 对象不可用（如 `reportAttributeAccessIssue` 被发现），以 `urllib.parse.urlparse` 替代路径分组。
- **通讯依赖的全局异常须保留**：凡经 `except Exception as e: pass` 静默之异常，并非冗余——在拓扑探查、多级备选路径、并发捕手语义下，此乃设计，当保留原形。不视为“待处理错误”而替为 logging 调用，若复引则上下文里须给同样覆写。

## 后台任务之律

- 后台任务以 `notify_on_complete=true` 运行，事毕自报
- 服务器启动后，以健康检查或日志信号验证就绪，再行后续操作

## 构建/安装之律

当用户以「你来 build」、「你来装」等指令授权操作时：

- **Python CLI 项目化**：若脚本以 `uv run --isolated --no-project --with ...` 临时取依赖，而用户令其改为最简 `uv project`，则先查 `uv run --help` 确认语义；继而以最小 `pyproject.toml` 写入 `project.name`、`version`、`requires-python`、`dependencies`；入口仅保留 `uv --directory <dir> run <script> "$@"`。落盘后须读回入口，确认 `--isolated` 与 `--no-project` 已绝迹，并实跑 CLI 至返回有效输出；`uv.lock` 与 `.venv` 乃验证所生，勿误判为手工产物。
- **先勘全链**：承命后第一件事勘全依赖，不手盲试。
  对 KataGo 等 CUDA 项目：必检 `which nvcc`、`nvcc --version`、`nvidia-smi`、`which cmake`、Arch 有无 `cuda` 包可用。
- **sudo 不可用时，降级为一键脚本**：若 `sudo` 缺终端而失败，不可仅回「阻塞」。须生成完整可执行脚本，令主君自运，并明示「存为 `setup.sh` 后 sudo bash 执行」。
- **CUDA toolkit 陷阱**：CUDA 常规 conda 获取有 ABI 之名，且不可默然行之。若讳言欲以 conda 规避 sudo，须先向用户申明利弊，得其允准。
- **权重/模型获取之律**：AI 引擎（KataGo 等）的权重文件常托管于境外 CDN（CloudFront、media.katagotraining.org），国内直连被 Cloudflare 拦截属常态。承命后：
  1. 先探 `curl -sIL ${URL} | head -20` 判 403/200
  2. 若 403，勿绕弯路（改镜像、换 CDN、自建代理等均不可行），直接告知用户此网络限制，请用户手动下载后放入目标目录
  3. 若用户已备妥文件，直接使用，不再追问来源
- **gh-proxy 仅用于 GitHub**：`v6.gh-proxy.org` 之 rewrite 只对 `https://github.com/` 生效，对 media.katagotraining.org、AWS CloudFront 等其他域名无效。配置后需验证实际效果。
- **搜索受阻时不钻牛角尖**：当 `web_search` 返回无关结果、`browser` 无法导航、`curl` 返回 403/404 时，勿反复搜索同义词。停步评估——是否有现成资源（用户已下载/本地已有/其他路径可获）？若无，直接告知用户当前网络限制即可。
- **`web_extract` 后端陷阱**：Hermes 的 `web_extract` 依赖 `web.extract_backend` 配置。若其后端为 SearXNG（默认情况），则**仅为搜索后端，无抓取能力**，调用时返回 `SearXNG is a search-only backend and cannot extract URL content`。此时应改用本地方案：① `curl` 或 `w3m -dump` 等文本浏览器获取 HTML，再经 Python `BeautifulSoup` + `markdownify` 转为 Markdown；② 或改用 `browser_navigate` + `browser_snapshot full=true`。若用户欲用本机 CRW 作抓取服务，按 Firecrawl 兼容后端接入，详见 `references/crw-firecrawl-hermes.md`。在配置 `firecrawl`/`tavily`/`exa`/`parallel` 等抓取后端前，此为本机无外部依赖的可行替代。
- **tini + YAML list command 之坑**：当 Docker 镜像以 `tini` 为 entrypoint 时，docker-compose 的 `command` 若写成 YAML list 形式（如 `- serve`），tini 会直接 exec 第一个元素（`serve`），而非将其作为子命令传给主程序。症状：`[FATAL tini] exec serve failed: No such file or directory`。修法：改用 shell 字符串形式（`command: lightpanda serve --host ...`），tini 会通过 `sh -c` 正确传递。
- **权重选择策略**：用户要求「最轻」时优先选 `*‑b10c128*` 或 `*‑b15c192*`；其次 `*‑b20c256*`；不可得时方选 `*‑b18c384*`。若列表无最小者，以当前可得的 `*‑b20c256x2*` 或 `*‑b18c384*` 为替代。勿因找不到理想模型而卡住整个流程。

### KataGo 构建与运行之律

- **缺子模块必先补**：`git clone --recurse-submodules` 或 `git submodule update --init --recursive`。`external/tclap-1.2.5`、`external/filesystem-1.5.8` 等均在 `cpp/external/` 下，非仓库根目录。
- **CUDA 后端编译**：```bash cmake -B build -S cpp -DUSE_BACKEND=CUDA -DCMAKE_BUILD_TYPE=Release -DNO_GIT_REVISION=1 && cmake --build build -j$(nproc) ``` 产物在 `build/katago`。
- **GTP 配置必带 resign 字段**：`gtp_minimal.cfg` 中 `allowResignation = false` 时仍需显式写 `resignThreshold` 与 `resignConsecTurns`，否则启动报 `Could not find key 'resignThreshold' in config file` 而崩溃。
- **`komi` 不可写在 gtp 配置中**：GTP 配置解析会警告 `Unused key 'komi'`。Komi 应由 GTP 前端通过 `komi` 命令设定，不在 `.cfg` 里硬编码。
- **KataGo GTP 守护陷阱**：KataGo 的 `gtp` 子命令读 stdin。若 stdin EOF（如用 pipe 传几条命令后断开、或 `nohup ... &` 后台化且无 tty），进程会正常退出。要保持常驻：① 用 GUI 前端（KaTrain、Lizzie）接管 GTP 管道；② 在前台终端交互运行；③ 用 `screen`/`tmux` 保持终端会话。
- **KataGo 必须配 GUI 前端**：KataGo 本身是 GTP 命令行引擎，无任何 UI。Arch 常用前端：`KaTrain`（`yay -S katrain`）、`Lizzie`（AUR）、`Sabaki`（`yay -S sabaki`）、`q5go`（`yay -S q5go`）。GUI 中填引擎路径与 config/model 路径即可。

## 安全之律

凡涉权限、属主、安全配置之改，依 **security-boundaries** 之律，必先请旨

## Git 隔离之律

- 凡涉代码之改，必先立独立 Worktree，严禁直改主目录

## 验证之律

凡改配置、更代码，必躬行验证——确保「启动成功、无报错、功能正常」方告完成。若验证失败，依查错之律回溯根因

- **TOML 语法须前置校验**：凡修改 yazi 等以 TOML 为配置之应用，补丁落盘后须先以工具确认「解析无误」，再启动程序。yazi 无单独 config-parse CLI，改后直接 `ya` 启动观察报错即可，切勿仅凭目视判断格式无误即视为完成
- **yazi `[open]` 须用 `rules` 数组，`[[open.rules]]` 非法**：`[[open.rules]]` 之 array-of-tables 写法在 yazi TOML 中非法，会报 `invalid type: map, expected a sequence`。正确写法为 `[open]` 单节，内嵌 `rules = [ { mime = "text/markdown", use = "glow" } ]`。凡改此节，须以 `ya` 启动验证，不可凭推测猜 schema
- **yazi `[opener.<name>]` 须为表（map）而非序列**：`[opener.glow]` 下须为键值对（`run`、`block`、`desc`），若以序列语法书写，会报 `invalid type: map, expected a sequence`。内置预设 `yazi-default.toml` 中 `[opener]` 各条目均为表
- **yazi `[opener.<name>]` 须为表（map）而非序列**：`[opener.glow]` 下须为键值对（`run`、`block`、`desc`），若以序列语法书写，会报 `invalid type: map, expected a sequence`。内置预设 `yazi-default.toml` 中 `[opener]` 各条目均为表
- **TUI 配置须以 tmux 操作验证**：对 yazi 等 TUI 应用，改配置后不可仅止于 TOML 语法校验或进程启动无报错。须在 tmux 中创建 session，用 `send-keys` 模拟用户操作（导航、Enter 触发 opener），以 `capture-pane` 截屏确认界面状态、`ps aux` 确认外部工具被调起。详见 `references/yazi-tmux-verification.md`
- **改配置前必先读 schema**：凡涉 TOML 配置（yazi、zellij、starship 等），不得凭推测猜写键名、表名与嵌套方式。应：① 查官方文档或 `--help`/`man`；② 再行补丁。连续猜 schema 并改出错误，是反复致文件全部无法打开的根因
- **用户报告「已破」时立即回退并验证**：若用户指出改动导致某功能不可用（如「不能 open 任何文件」），第一动作应是按原内容回退文件；回退后须自验「默认行为复归」，再向用户确认。切不可在未回退状态下继续叠加新 patch 猜测修复

## Lisp 项目目录之律

用户以 `~/code/` 作为所有源码仓库（含 `git clone` 目标）之根目录。凡涉 Lisp/Quicklisp 项目，遵循以下组织：

- **源码**：`~/code/<project>/`
- **Quicklisp local-projects**：以 symlink 指向 `~/code/<project>/`，而非相反
- **Quicklisp 本体**：`~/quicklisp/`（上游惯例，不动）
- **严禁**：在 `~/` 下散落 `.lisp`、`.sexp`、`setup.lisp`、`asdf.lisp` 等临时文件；快速安装后若不净，立刻清理

## 功能卸载之律

凡用户要求「禁用」「卸载」或「移除」某功能时：

- **先辨源码与产物**：`src/`、`ui-tui/src/`、`hermes-agent/**/*.py` 等属源码，不可擅删除；`node_modules/`、`dist/`、`build/`、`venv/` 等属构建产物，可安全清理
- **TUI 卸载安全路径**：Hermes TUI（`ui-tui/`）之 `node_modules/` 与 `dist/` 可整目录删除，核心 agent（`venv/bin/hermes`，Python）不受影响。删除後 `hermes --version`、`hermes status` 应正常
- **问清楚再动手**：若用户只说「卸载」而未指明范围，默认只清构建产物，不动源码

## 终端 UI（TUI）之律

Hermes TUI 基于 Ink（React for CLI），运行在终端 raw mode 下，有如下限制：

- **剪贴板真空**：raw mode 截获 Ctrl+C 为 SIGINT（退出信号），终端模拟器无法执行原生复制。TUI 若未显式处理 clipboard，则复制功能不可用
- **变通三径**：① 终端层叠加高亮（部分终端支持 bypass raw mode 选中）；② 退出後从 `~/.hermes/logs/` 或 `hermes logs` 取回内容；③ 长文 copy/paste 场景改用 `hermes chat` 或 `hermes -z`，CLI 沿用终端原生复制
- **根治须动源码**：若欲修复，须在 `ui-tui/src` 全局快捷键监听处拦截 Ctrl+C，优先写 `clipboard.writeText()` 而非抛 SIGINT——此非配置项，属代码级改动

## 超时与审批之律

- `approvals.timeout`：终端工具发出的危险命令审批超时
- `clarify.timeout`：Agent 主动向用户发问的等待超时
- 两者不可混用。如需长时间无人值守操作，调整前者

## 技能合并之律

遇两技能内容重叠时，循以下之序：

- **辨**：细阅两文，列出重叠与差异之处
- **定**：选详备者为主文，简略者为辅
- **削**：删主文中冗余之节，辅文改为一行援引
- **泛**：示例中具体人名、路径换为泛指，毋留会话之痕
- **验**：合并后自问——是否尚有重复？是否援引清晰？
