---
name: yazi-config
description: 凡修改 yazi 等 TUI 的 TOML 配置、并需验证其真能生效时，即当加载。
---

# TUI 配置之律

## 改前必读 schema

凡涉 TOML 配置（yazi、zellij、starship 等），不得凭推测猜键名、表名与嵌套方式。先查官方文档或 `--help` / `man`，再落补丁。连续猜 schema 改出错误，是反复致文件全部无法打开的根因。

## yazi 已知 schema 坑

- **`[open]` 须用 `rules` 数组**：`[[open.rules]]` 之 array-of-tables 写法非法，报 `invalid type: map, expected a sequence`。正确写法：

  ```toml
  [open]
rules = [ { mime = "text/markdown", use = "glow" } ]
  ```

- **`[opener.<name>]` 须为表（map）而非序列**：`[opener.glow]` 下须是键值对（`run`、`block`、`desc`）。内置预设 `yazi-default.toml` 中 `[opener]` 各条目均为表。

## 验证到界面，不止于语法

TOML 语法校验或「进程启动无报错」都不算验证完成。须在 tmux 中建 session，用 `send-keys` 模拟导航与 Enter 触发 opener，以 `capture-pane` 截屏确认界面状态、`ps aux` 确认外部工具被调起。详见 `references/yazi-tmux-verification.md`。

## 用户报「已破」时

若用户指出改动导致功能不可用（如「不能 open 任何文件」），第一动作是按原内容回退文件，回退后自验默认行为复归，再向用户确认。不可在未回退状态下继续叠加新 patch 猜修复。
