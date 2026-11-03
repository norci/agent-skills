---
name: docker-host-access
description: 凡需容器访问宿主机服务、配置 host-gateway 时，即当加载。
---

# 容器访宿主机之道

## 症结
容器内 127.0.0.1 指容器自身，非宿主机。需访宿主机代理、数据库时，当另辟蹊径。

## 解法

**docker-compose.yaml**:
```yaml
services:
  myservice:
    extra_hosts:
    - "host.docker.internal:host-gateway"
```

**host 网络**: `network_mode: host` — 容器共享宿主机网络栈，不须转址，直访 `localhost:<port>`。省心，但牺牲端口隔离。

应用中以 `host.docker.internal` 为宿主机地址。

## 须要绑 0.0.0.0 时

**host 网络**：`network_mode: host` — 容器共享宿主机网络枣，不须转址，直访 `localhost:<port>`。省心，但牺牲端口隔离。

应用中以 `host.docker.internal` 为宿主机地址。

## 须要绑 0.0.0.0 时

宿主机服务若只监 `127.0.0.1`，则容器即便用 host 网络仍可访问；但若日后改桥接，则需服务端改绑 `--host 0.0.0.0`（配套鉴权或防火墙，勿裸开）。

## 要义

- **Linux**：`host.docker.internal` 默认不解析，必加 `extra_hosts`（或 `network_mode: host`）
- `host-gateway` 为 Docker 20.10+ 特殊值，解析为宿主机 IP
- 务加引号，防 YAML 误解析冒号
- **Open WebUI 必设 `WEBUI_SECRET_KEY`**，否则容器退出（`openssl rand -hex 32`，非交互可写 `.env` 后 `--env-file`）
- **非交互环境禁用登录**：`WEBUI_AUTH=false` 避免 OAuth 跳转卡住（仅适用于受网络隔离的演示/私有部署）
- **Open WebUI 必设 `WEBUI_SECRET_KEY`**，否则容器退出（`openssl rand -hex 32`，非交互可写 `.env` 后 `--env-file`）。
- **非交互环境禁用登录**: `WEBUI_AUTH=` 避免 OAuth 跳转卡住（仅适用于受网络隔离的演示/私有部署）。

## 与 Hermes 搭配实例

Docker 跑 Open WebUI 对接宿主机 Hermes 实例：
- Hermes API Server 适配器监听 `127.0.0.1:8642`。
- Open WebUI 容器用 `network_mode: host` 后，`OPENAI_API_BASE_URL=http://localhost:8642/v1` 即可直连宿主机 8642 端口。
- 若不用 host 网络，须 `extra_hosts` 并让 Hermes 监听 `0.0.0.0:8642`。

## 代理配置

SOCKS 代理用 `socks5h://`（非 `socks5://`），DNS 亦走代理，防泄漏:
```yaml
outgoing:
  proxies:
    all://:
    - socks5h://host.docker.internal:10801
```

## 验证

```bash
docker compose config                         # 验 YAML
docker exec <container> nc -zv host.docker.internal <port>  # 验连通
```
