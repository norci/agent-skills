---
name: python-script-ops
description: 凡写会联网或读凭证的 Python 脚本、或把临时脚本改成 uv 项目时，即当加载。
---

# Python 脚本工程之律

## 代理显式声明

创建 `httpx.Client` / `httpx.AsyncClient` 时显式传 `proxy=None`，阻断默认代理链路。禁绝「任凭 httpx 依系统环境变量决策」——尤其在 MITM 或容器环境中全局 `ALL_PROXY` 指向 SOCKS 服务、而本机未装 `socksio` 时，会直接 ImportError 崩溃。

若全局 `httpx.URL` 不可用，以 `urllib.parse.urlparse` 替代路径分组。

## 通讯依赖的全局异常须保留

`except Exception as e: pass` 并非冗余。在拓扑探查、多级备选路径、并发捕手语义下，此乃设计，当保留原形；不视为「待处理错误」而替为 logging。

## 凭证取自 pass 的 stdout

若 `pass show <entry>` 是某凭证之源，脚本须直接 capture stdout 读完整值。仅见脱敏形式（如 `sk-34e...243e`）时不可将其写入磁盘视为完整 key——脱敏版会导致 401，却让脚本在「看起来有 key」的路上越走越远。用户已明言「用 pass show 读 key」时，subprocess 调用即主路径，`key.yaml` 之类仅作 optional fallback。

## 重量级假设须先验证

外部 API key、代理方案、依赖可用性（`httpx[socks]`、`socksio`、`pip` 缺失）等不可假定存在。先以最小探测（`which`、读环境、`import` 测试）确认，再选路径。全部未具足时直告用户阻塞点与修复动作。

## 脚本改 uv 项目

用户令临时脚本（`uv run --isolated --no-project --with ...`）改为最简 `uv project` 时：先查 `uv run --help` 确认语义，再以最小 `pyproject.toml` 写 `project.name`、`version`、`requires-python`、`dependencies`，入口仅留 `uv --directory <dir> run <script> "$@"`。落盘后读回入口确认 `--isolated` 与 `--no-project` 已绝迹，并实跑 CLI 至返回有效输出。`uv.lock` 与 `.venv` 乃验证所生，勿误判为手工产物。

## rm 超时之患

`rm -rf` 于特定路径下偶发超时，补救：以 `shutil.rmtree()` 替代。
