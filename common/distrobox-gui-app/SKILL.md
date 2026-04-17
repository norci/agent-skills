---
name: distrobox-gui-app
description: 建 Distrobox 容器、配 NVIDIA GPU、在容器里装 GUI 应用时用。
---

# Distrobox 里装 GUI 应用

## 选镜像

| 用途 | 镜像 | 理由 |
|---|---|---|
| 钉钉 | `ubuntu:latest` | 钉钉 `.deb` 在 Ubuntu 上兼容性最好 |
| 通用开发 | `debian:testing` | 包更全，可换清华源加速 |

Debian Testing 的 GLib / Pango / HarfBuzz 版本与钉钉期望不合，运行时报符号错误（如 `hb_ot_metrics_get_position` 未定义）。钉钉一律用 Ubuntu 镜像。

## 建容器

```bash
distrobox create --name dingtalk-box --image ubuntu:latest --nvidia
distrobox create --name debian-gpu --image debian:testing --nvidia
```

要容器内直接拿到 root 时加 `--root`，隔离性随之下降，只在可信镜像上用。

## 等初始化结束

容器创建后宿主机 `ps` 里会有 `apt-get` 进程在装基础包，通常 2–5 分钟。等它跑完；杀它会留下装了一半的容器。

## 换源（Debian Testing）

Debian 12 起源文件是 DEB822 格式的 `/etc/apt/sources.list.d/debian.sources`，改 `/etc/apt/sources.list` 不生效。先备份再写：

```bash
podman exec -u 0 <container> cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
```

清华源内容：

```
Types: deb
URIs: http://mirrors.tuna.tsinghua.edu.cn/debian
Suites: testing testing-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp

Types: deb
URIs: http://mirrors.tuna.tsinghua.edu.cn/debian-security
Suites: testing-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.pgp
```

用 HTTP 是因为容器里还没有 `ca-certificates`，装好后可改回 HTTPS。`Components` 必须含 `contrib`、`non-free`、`non-free-firmware`。

```bash
podman exec -u 0 <container> apt-get update -y
```

## 装中文字体与 Electron 依赖

```bash
podman exec -u 0 <container> apt-get install -y \
  fonts-noto-cjk fonts-wqy-microhei fonts-wqy-zenhei fonts-arphic-uming \
  libxss1 libasound2t64 libnss3 libxcomposite1 libxdamage1 libxrandr2 libpango-1.0-0 libsm6
```

Debian Testing 的 `libasound2` 已改名为 `libasound2t64`，Ubuntu 上仍可能是 `libasound2`。包名对不上时用 `apt-cache search <name>` 查。`libsm6` 是钉钉的硬依赖（`libSM.so.6`）。

## 装钉钉

```bash
podman exec -u 0 <container> apt-get install -y /path/to/com.alibabainc.dingtalk_*.deb
podman exec -u 0 <container> apt-get install -f    # 缺依赖时补
```

钉钉把私有库放在 `/opt/apps/...` 下，启动前必须把该目录和 `plugins/dtwebview` 加进 `LD_LIBRARY_PATH`：

```bash
APP_DIR="/opt/apps/com.alibabainc.dingtalk/files/8.1.0-Release.6021101"
LD_LIBRARY_PATH="${APP_DIR}:${APP_DIR}/plugins/dtwebview:$LD_LIBRARY_PATH" \
  distrobox enter <container> -- "${APP_DIR}/com.alibabainc.dingtalk" &
```

同目录的 `dingtalk_shell` 同样要设 `LD_LIBRARY_PATH`。钉钉自带 `libssl.so.1.1`，不要用系统 `libssl3` 顶替，让 `LD_LIBRARY_PATH` 指过去即可。报沙箱错误时加 `--no-sandbox`。

## 启其它 GUI 应用

```bash
distrobox enter <container> -- <app-command>
```

## 验收

```bash
distrobox enter <container> -- nvidia-smi                              # GPU
distrobox enter <container> -- fc-list | grep -i 'noto\|wqy\|arphic'   # 中文字体
distrobox enter <container> -- <app-command> --version
```

## 坑

| 现象 | 因 | 处置 |
|---|---|---|
| `apt-get` 卡在锁上 | 容器初始化正在装基础包 | 等；非初始化时长期阻塞才考虑杀，杀有风险 |
| `distrobox enter` 在非交互脚本里挂住 | enter 走 FIFO | 非交互任务改用 `podman exec -u 0 <container> <cmd>` |
| 改 `/etc` 报权限不足 | `distrobox enter` 以普通用户入 | `podman exec -u 0` 或 `distrobox enter --root` |
| 找不到包 | Testing 的库转 t64 后改名 | `apt-cache search <name>` 确认现名 |
| HTTPS 验签失败 | 容器里没有 CA 证书 | 换源先用 HTTP，装好 `ca-certificates` 再改回 |