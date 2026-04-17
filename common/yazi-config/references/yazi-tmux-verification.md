# Yazi 配置之 tmux 验证法

## 适用场景

修改 yazi 的 `~/.config/yazi/yazi.toml` 后，需在真实 TUI 环境中验证配置生效，而非仅靠 TOML 解析校验或 `ya --help`。

## 关键命令速查

```bash
# 创建 tmux session 以 yazi 启动
tmux new-session -d -s yazi-test -x 120 -y 30 'cd /tmp && yazi'

# 等待渲染
sleep 1.5

# 在 yazi 内导航（方向键/j/k/G 等）
tmux send-keys -t yazi-test 'j'

# 按 Enter 触发 opener
tmux send-keys -t yazi-test Enter

# 截屏验证当前 pane 输出
tmux capture-pane -t yazi-test -p

# 检查外部进程（glow 等）是否被 yazi 调起
ps aux | grep -E '[g]low|yazi' | grep -v grep

# 清理
tmux kill-session -t yazi-test
```

## 工作流

1. **改配置** → `write_file` / `patch`，然后以 Python `tomllib` 校验 TOML 语法：
   ```bash
   python3 -c "import tomllib; f=open('$HOME/.config/yazi/yazi.toml','rb'); tomllib.load(f); print('OK')"
   ```
2. **准备测试文件**（如 opener 测试需有 `.md` 文件在目标目录）
3. **启动 tmux session**，确认 yazi 渲染正常（无 TOML parse error 退出）
4. **模拟操作**：`send-keys` 导航到目标文件 → `Enter` → `capture-pane` 确认状态
5. **验证外部工具**：`ps aux | grep glow` 确认被调起（glow 闪屏退出后只有 yazi 存活也算通过）
6. **清理 session**

## 陷阱

- yazi 的 `[open]` 配置语法是 `[open]` 表 + `rules = [ { ... } ]` 数组，**非** `[[open]]` 数组表。后者报 `invalid type: sequence, expected a map`
- 若 `send-keys` 后 `capture-pane` 看不到变化，可能是指令未发出或 yazi 未渲染完。先 `sleep 1.5` 确保 yazi 已启动，再发送按键
- `glow` 渲染后自动退出返回 yazi，属正常行为。ps 中 glow 短暂出现后消失、yazi 仍在运行即为成功