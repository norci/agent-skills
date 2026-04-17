---
name: distrobox-gui-app
description:凡需创建 Distrobox 容器、配置 NVIDIA GPU、安装 GUI 应用，即当加载。
tags: [distrobox, nvidia, gui, dingtalk, debian, ubuntu, electron, chinese-fonts]
---

# Distrobox GUI 容器之道

立 Distrobox 容器，启 NVIDIA GPU，安中文字体与 Electron 运行之依，并以钉钉为例演示 GUI 应用安装与启动

---

## 一、择镜像

| 用途 | 推荐镜像 | 理由 |
|------|---------|------|
| 钉钉专用 | `ubuntu:latest` | 钉钉 `.deb` 包在 Ubuntu 上兼容性最佳 |
| 通用开发 | `debian:testing` | 包更全，可配清华镜像源加速 |

### 警
- Debian Testing 上宿 GLib/Pango/HarfBuzz 版本与钉钉期望不尽相容，易致符号错误（如 `hb_ot_metrics_get_position`）.**钉钉建议用 Ubuntu 镜像**
- Debian 12 (bookworm) 改用 DEB822 格式（`/etc/apt/sources.list.d/debian.sources`），旧法改 `sources.list` 无效

---

## 二、立盒

### Ubuntu（推荐钉钉）
```bash
distrobox create --name dingtalk-box --image ubuntu:latest --nvidia
```

### Debian Testing + NVIDIA
```bash
distrobox create --name debian-gpu --image debian:testing --nvidia
```

### 备：常驻 root 之盒
```bash
distrobox rm <name> -f
distrobox create --name <name> --image ubuntu:latest --nvidia --root
```
然则隔离性减，慎用于不托之地

---

## 三、待初始化毕

容器创建后，观宿主机 `ps` 中是否有 `apt-get` 进程运行。等候毕（常需 2–5 分钟）

**切勿杀该进程**，否则容器异常

---

## 四、配源（Debian Testing 专用）

Debian Testing 以 DEB822 格式存于 `/etc/apt/sources.list.d/debian.sources`。以 root 入，备份并编辑之：

```bash
podman exec -u 0 <container> cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
```

填入以下清华源内容：

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

### 注
- 用 HTTP 免 SSL 证书之恼，日后安 `ca-certificates` 后可改回 HTTPS
- 须含 `contrib`, `non-free`, `non-free-firmware` 组件

---

## 五、更新包索引

```bash
podman exec -u 0 <container> apt-get update -y
```

---

## 六、安字体与 Electron 依

中文字体与 Electron GUI 应用通用依赖：

```bash
podman exec -u 0 <container> apt-get install -y \
 fonts-noto-cjk \
 fonts-wqy-microhei \
 fonts-wqy-zenhei \
 fonts-arphic-uming \
 libxss1 \
 libasound2t64 \
 libnss3 \
 libxcomposite1 \
 libxdamage1 \
 libxrandr2 \
 libpango-1.0-0 \
 libsm6
```

### 要
- Debian Testing 中 `libasound2` 已转 `libasound2t64`
- Ubuntu 上包名可能略有不同（如 `libasound2` 而非 `libasound2t64`），以 `apt-cache search` 查证
- `libsm6` 为钉钉所需（`libSM.so.6`）

---

## 七、安钉钉（示例 GUI 应用）

### 安装 .deb 包
```bash
podman exec -u 0 <container> apt-get install -y /path/to/com.alibabainc.dingtalk_*.deb
```

若依缺失，补：
```bash
podman exec -u 0 <container> apt-get install -f
```

### 启动钉钉（关键：LD_LIBRARY_PATH）
钉钉将私有库置于 `/opt/apps/...`，启动时须设 `LD_LIBRARY_PATH` 指向该目录及 `plugins/dtwebview`：

```bash
APP_DIR="/opt/apps/com.alibabainc.dingtalk/files/8.1.0-Release.6021101"
LD_LIBRARY_PATH="${APP_DIR}:${APP_DIR}/plugins/dtwebview:$LD_LIBRARY_PATH" \
distrobox enter <container> -- "${APP_DIR}/com.alibabainc.dingtalk" &
```

亦可使用 `dingtalk_shell`（同目录），然同样须设 `LD_LIBRARY_PATH`

### 警
- **libssl 版本**：勿试图用系统 libssl3 替代，钉钉自带 `libssl.so.1.1`，以 `LD_LIBRARY_PATH` 指引即可
- 若遇沙箱错误，加 `--no-sandbox`

---

## 八、启任意 GUI 应用

```bash
distrobox enter <container> -- <app-command>
```

---

## 九、检视

```bash
# NVIDIA GPU 检测
distrobox enter <container> -- nvidia-smi

# 中文字体检测
distrobox enter <container> -- fc-list | grep -i 'noto\|wqy\|arphic'

# 应用版本
distrobox enter <container> -- <app-command> --version
```

---

## 警汇总

- **apt/dpkg 锁冲突**：容器初始化自装基础包时常占锁，宜等待。若非初始化而长阻塞，可手动杀之，然有风险
- **podman exec 之利**：bypass `distrobox enter` 的 FIFO 限制，于非交互任务更稳
- **非 root 入**：`distrobox enter` 以普通用户入，无权限改 `/etc` 配置。此时宜用 `podman exec -u 0` 或 `distrobox enter --root`
- **包名变迁**：Testing 之库多转 t64，查包时用 `apt-cache search <name>` 确认
- **HTTP 的风险**：容器内少 CA 证书，HTTPS 易验签失败；HTTP 虽不安全，然于内网镜像可接受
- **DEB822 源格式**（Debian Testing）：须改 `debian.sources`，非 `sources.list`
- **Ubuntu 镜像与钉钉**：兼容性更优，Debian Testing 的 GLib/Pango/HarfBuzz 版本易致符号错误

---

## 版本记录

| 日期 | 说明 |
|------|------|
| 2026-04-22 | 初稿（自 dingtalk-on-distrobox、distrobox-debian-nvidia 合并） |
