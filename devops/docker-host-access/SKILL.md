---
name: docker-host-access
description:凡需容器访问宿主机服务、配置 host-gateway 时，即当加载。
---

# 容器访宿主机之道

## 症结
容器内 `127.0.0.1` 指容器自身，非宿主机。需访宿主机代理、数据库时，当另辟蹊径

## 解法

**docker-compose.yaml**：
```yaml
services:
  myservice:
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

应用中以 `host.docker.internal` 为宿主机地址

## 要义

- **Linux**：`host.docker.internal` 默认不解析，必加 `extra_hosts`
- `host-gateway` 为 Docker 20.10+ 特殊值，解析为宿主机 IP
- 务加引号，防 YAML 误解析冒号

## 代理配置

SOCKS 代理用 `socks5h://`（非 `socks5://`），DNS 亦走代理，防泄漏：
```yaml
outgoing:
  proxies:
    all://:
      - socks5h://host.docker.internal:10801
```

## 验证

```bash
docker-compose config # 验 YAML
docker exec <容器> nc -zv host.docker.internal <端口> # 验连通
```
