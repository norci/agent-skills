---
name: ironclaw-port-config
description:凡涉 ironclaw 端口冲突、webhook_server 配置，即当加载。
---

# ironclaw 端口配置之法

## 问题
运行 `ironclaw run` 时报错：
```
✗ Channel webhook_server failed to start: Failed to bind to 127.0.0.1:8080: Address already in use (os error 98)
```

## 误区
误以为可用 `ironclaw config set channels.gateway_port <port>` 改 webhook_server 端口。实则此配置仅影响 gateway 通道，非 webhook_server

## 正解
webhook_server 端口由环境变量 `HTTP_PORT` 控制，默认 8080

### 临时修改
```bash
HTTP_PORT=8081 ironclaw run
```

### 永久修改
```bash
echo 'export HTTP_PORT=8081' >> ~/.bashrc
source ~/.bashrc
```

## 验证
```bash
HTTP_PORT=8081 timeout 5 ironclaw run 2>&1 | grep "gateway"
```
当显：`gateway http://127.0.0.1:8081/?token=***`

## 相关环境变量
- `HTTP_PORT` —— webhook_server 端口 (默认 8080)
- `HTTP_HOST` —— webhook_server 绑定地址 (默认 127.0.0.1)
- `HTTP_WEBHOOK_SECRET` —— webhook 共享密钥

## 排查步骤
1. 确认端口占用：`ss -tlnp | grep <port>`
2. 查占用进程：`fuser <port>/tcp` 或 `ps aux | grep <process>`
3. 设环境变量：`export HTTP_PORT=<new_port>`
4. 运行 ironclaw：`ironclaw run`

## 注意
- `ironclaw config set channels.gateway_port` 仅影响 gateway 通道 (默认 3000)，非 webhook_server
- webhook_server 端口硬编码于源码，唯环境变量可覆
- 若 8080 被 SearXNG 或其他服务占用，必改此环境变量
- 查官方仓库为 `nearai/ironclaw`，非 `JoasASantos/ironclaw` (旧版 v0.2.0)
