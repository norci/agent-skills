---
name: linux-desktop-integration-triage
description: 桌面程序集成失效，或要查进程实际环境与已载库时用。
---

# 集成失效之诊

## 先分层，勿查症状

桌面集成皆三段：**客户端 → 协议 → 服务端**。

| 层 | 谁 | 取证 |
|---|---|---|
| 客户端 | 目标进程 | `/proc/<pid>/exe`、`maps`、`environ` |
| 协议 | XIM、Wayland text-input、DBus、StatusNotifier、portal | `strings <bin>` 内有无该协议之符号 |
| 服务端 | fcitx5、合成器、portal、dbus daemon | 服务端自有诊断，列已连入之客户端 |

症状（打不出字、托盘不见、缩放错）从来不在故障那一层。**先问服务端此刻见谁**：服务端未列目标进程，即客户端从未建立连接，与表现无关。

## 证取自进程，不取自信

配置之值、文档所述、shell 中 `env` 之输出，皆非进程实际所得。进程之环境取 `/proc/<pid>/environ`（`tr '\0' '\n'` 读之），库取 `/proc/<pid>/maps`。

- 教训：文档言 `XMODIFIERS=@im=fcitx` 足矣；进程中此变量确在，而决定 Qt 程序选何输入插件之 `QT_IM_MODULE` 为空，遂静默退回 `compose`，全程无报错。

## 静态链接者自带宽

`ldd` 未见 `libQt*`、`libgtk*`，不等于无其能力，只说明能力编入二进制，**系统插件目录对它无效**。

判法：`strings <bin>` 查工厂与协议符号（`QPlatformInputContextFactory`、`XOpenIM`、`XIM_SERVERS`、`wl_display_connect`）。见工厂而无 XIM 符号者，必由环境变量择插件，且只可择二进制内嵌之少数。

## 最小对照实验定案

取临时 `HOME` 与 `XDG_RUNTIME_DIR`，只加待验之一变量，启一实例，观服务端是否多出一条连接。见则定案，不必再推。

- 收尾前以此法定修复：服务端列出新客户端，方为验过。
- 实验目录用讫即删；实验进程与原进程须以 pid 分清。

## 取 pid 与路径之戒

- `pgrep -f <名>` 常命中同类影子进程（`crashpad_handler`、`zygote`、包装脚本），据其 `maps` 会得出「未载任何库」之谬论。当以 `for p in $(pgrep -f <名>); do readlink /proc/$p/exe; done` 筛出真主进程。
- 杀进程按 pid。**勿按 AppImage 路径或挂载词杀**：FUSE 宿主一死，`/tmp/.mount_*` 即卸载，程序失了文件与窗口，用户须重启。
- AppImage 挂载点每次启动改名，凡用路径处当场取（`ls -d /tmp/.mount_*`），勿写死。

## 修在最小范围

改用户级 desktop 之 `Exec`（`Exec=env VAR=val /path/app`）优于改 `/etc/environment` 或会话环境：只及此程序，不惊其余客户端，亦避发行版之告警。

验收三事：进程环境有该变量、服务端列有该客户端、窗口在其后端正常。三者同立方为修复。
