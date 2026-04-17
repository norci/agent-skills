---
name: katago-build
description: 构建或运行 KataGo 时用。
---

# KataGo 构建与运行

## 先勘全链

承命后第一件事勘全依赖，不手盲试。必检 `which nvcc`、`nvcc --version`、`nvidia-smi`、`which cmake`，以及 Arch 有无 `cuda` 包可用。

## 缺子模块必先补

`git clone --recurse-submodules`，或事后 `git submodule update --init --recursive`。`external/tclap-1.2.5`、`external/filesystem-1.5.8` 等在 `cpp/external/` 下，不在仓库根目录。

## CUDA 编译

```bash
cmake -B build -S cpp -DUSE_BACKEND=CUDA -DCMAKE_BUILD_TYPE=Release -DNO_GIT_REVISION=1 && cmake --build build -j$(nproc)
```

产物在 `build/katago`。

## CUDA toolkit 陷阱

conda 装的 CUDA toolkit 有 ABI 问题，且不可默然行之。若欲以 conda 规避 sudo，须先向用户申明利弊并得其允准。

## 权重获取

权重托管于境外 CDN（CloudFront、media.katagotraining.org），国内直连常被 Cloudflare 拦截：

1. 先 `curl -sIL ${URL} | head -20` 判 403/200。
2. 若 403，勿绕弯路（改镜像、换 CDN、自建代理均不可行），直接告知用户此网络限制，请其手动下载后放入目标目录。
3. 用户已备妥文件则直接用，不再追问来源。
4. `v6.gh-proxy.org` 之类 rewrite 只对 `https://github.com/` 生效，对 media.katagotraining.org、AWS CloudFront 无效。

## 权重选择

用户要求「最轻」时优先 `*-b10c128*`，其次 `*-b15c192*`，再次 `*-b20c256*`，不可得方选 `*-b18c384*`。勿因找不到理想模型而卡住整个流程。

## GTP 配置

- **必带 resign 字段**：`allowResignation = false` 时仍需显式写 `resignThreshold` 与 `resignConsecTurns`，否则启动报 `Could not find key 'resignThreshold' in config file` 而崩溃。
- **`komi` 不可写在 gtp 配置中**：解析会警告 `Unused key 'komi'`。Komi 由 GTP 前端以 `komi` 命令设定。
- **stdin EOF 即退出**：KataGo 的 `gtp` 子命令读 stdin，stdin 一断（pipe 传几条命令后断开、或 `nohup ... &` 后台化且无 tty）进程即正常退出。要常驻须：① 用 GUI 前端（KaTrain、Lizzie）接管 GTP 管道；② 前台终端交互运行；③ `screen` / `tmux` 保活。

## GUI 前端

KataGo 本身是 GTP 命令行引擎，无 UI。Arch 常用前端：KaTrain（`yay -S katrain`）、Lizzie（AUR）、Sabaki（`yay -S sabaki`）、q5go（`yay -S q5go`）。GUI 中填引擎路径与 config/model 路径即可。

## sudo 不可用时

若 `sudo` 缺终端而失败，不可只回「阻塞」。须生成完整可执行脚本，令用户自行 `sudo bash setup.sh` 执行，并说明这一点。
