---
name: docker-host-access
description: 容器要访问宿主机服务、配 host-gateway 时用。
---

# 容器访宿主机之道

## 症结

容器内 127.0.0.1 指容器自身，非宿主机。需访宿主机代理、数据库时，当另辟蹊径。

## 解法

**docker-compose.yaml**：

```yaml
services:
  myservice:
    extra_hosts:
    - "host.docker.internal:host-gateway"
```

**host 网络**：`network_mode: host` 让容器共享宿主机网络栈，不须转址，直访 `localhost:`。省心，但牺牲端口隔离。

应用中以 `host.docker.internal` 为宿主机地址。

## 须要绑 0.0.0.0 时

宿主机服务若只监 `127.0.0.1`，用 host 网络仍可访问；但若改桥接，则需服务端改绑 `--host 0.0.0.0`（配套鉴权或防火墙，勿裸开）。

## 要义

- **Linux**：`host.docker.internal` 默认不解析，必加 `extra_hosts`（或 `network_mode: host`）。
- `host-gateway` 为 Docker 20.10+ 特殊值，解析为宿主机 IP。
- 务加引号，防 YAML 误解析冒号。

## 代理配置

SOCKS 代理用 `socks5h://`（非 `socks5://`），DNS 亦走代理，防泄漏：

```yaml
outgoing:
  proxies:
    all://:
    - socks5h://host.docker.internal:10801
```

## 容器编排之坑

**tini + YAML list command**：镜像以 `tini` 为 entrypoint 时，docker-compose 的 `command` 写成 YAML list（如 `- serve`）会让 tini 直接 exec 第一个元素，症状 `[FATAL tini] exec serve failed: No such file or directory`。改用 shell 字符串形式（`command: lightpanda serve --host ...`），tini 会经 `sh -c` 正确传递。

## 验证

```bash
docker compose config                                          # 验 YAML
docker exec <容器> nc -zv host.docker.internal <端口>            # 验连通
```

## Open WebUI 实例

- 必设 `WEBUI_SECRET_KEY`（`openssl rand -hex 32`），缺它容器启动即退出；非交互环境写进 `.env` 再用 `--env-file`。
- 受网络隔离的私有部署可设 `WEBUI_AUTH=false`，免去 OAuth 跳转卡住登录。
- 对接宿主机 Hermes：Hermes API Server 适配器监听 `127.0.0.1:8642`。容器用 `network_mode: host` 时 `OPENAI_API_BASE_URL=http://localhost:8642/v1` 直连；不用 host 网络则须 `extra_hosts`，并让 Hermes 改监听 `0.0.0.0:8642`。
