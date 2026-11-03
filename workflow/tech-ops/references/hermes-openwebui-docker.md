# Hermes + Open WebUI (Docker)

## 前提

- 本机已安装 Hermes Agent（源码位于 `~/.hermes/hermes-agent/`）
- Docker 与 Docker Compose 已就位
- 目标：用 Docker 跑 Open WebUI 容器，指向本机 Hermes 内置 API Server

## Hermes API Server

源码路径：`gateway/platforms/api_server.py`

- 适配器名：`APIServerAdapter`，注册于 `Platform.API_SERVER`
- 默认监听：`127.0.0.1:8642`（环境变量 `API_SERVER_PORT` 可改）
- 依赖：`aiohttp`（gateway 已自带）
- 鉴权：`API_SERVER_KEY` 环境变量；容器内任意非空 `OPENAI_API_KEY` 均可，Hermes 侧只要求 Bearer 非空

### 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI Chat Completions 格式（SSE streaming）|
| POST | `/v1/responses` | OpenAI Responses API 格式 |
| GET | `/v1/responses/{id}` | 取回存储的 response |
| DELETE | `/v1/responses/{id}` | 删除 response |
| GET | `/v1/models` | 列出可用模型 |
| GET | `/v1/capabilities` | 机器可读的 API 能力描述 |
| GET | `/api/sessions` | 列出 Hermes 会话 |
| POST | `/api/sessions` | 创建空会话 |
| GET/PATCH/DELETE | `/api/sessions/{id}` | 读/更新/删除会话 |
| GET | `/api/sessions/{id}/messages` | 会话消息历史 |
| POST | `/api/sessions/{id}/fork` | 分支会话 |
| POST | `/api/sessions/{id}/chat[/stream]` | 与持久化会话聊天 |
| POST | `/v1/runs` | 启动 run（202 立即返回 run_id）|
| GET | `/v1/runs/{id}` | 取回 run 状态 |
| GET | `/v1/runs/{id}/events` | SSE 结构化生命周期事件 |
| POST | `/v1/runs/{id}/approval` | 处理 pending 审批 |
| POST | `/v1/runs/{id}/stop` | 中断运行中 agent |
| GET | `/health` | 健康检查 |
| GET | `/health/detailed` | 详细状态（供跨容器 dashboard 探测）|

### 会话连续性

- `X-Hermes-Session-Id` request header：opt-in 会话延续
- `X-Hermes-Session-Key` request header：opt-in 长期记忆作用域

## Docker Compose 模板

放置于 `~/code/dockerfiles/hermes-openwebui/docker-compose.yaml`。

```yaml
services:
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    network_mode: host   # 关键：容器内 localhost 即宿主机
    volumes:
      - ./data:/app/backend/data
    environment:
      - OPENAI_API_BASE_URL=http://localhost:8642/v1
      - OPENAI_API_KEY=h-hermes-local   # 任意非空，Hermes 侧须有 API_SERVER_KEY
      - OAUTH_COOKIE_DOMAIN=
      - ENABLE_REGISTRATION=false
      - WEBUI_AUTH=false   # 本地测试可关认证；公网暴露须启
```

## 启动与验证

```bash
cd ~/code/dockerfiles/hermes-openwebui
docker compose up -d          # 后台启动
curl -s http://localhost:8080  # Open WebUI 页面
curl -s http://localhost:8642/health  # Hermes API Server 健康
```

## 关键约束与变体

- **单机同址**：`network_mode: host` 可通；容器内 `localhost:8642` 直抵宿主机 Hermes
- **跨址/多容器**：改用 `ports` 映射，并将 Hermes 监听地址改为 `0.0.0.0:8642`
- **Hermes 侧须开启 API Server**：`hermes gateway run --platforms api_server` 或 gateway 配置中包含 `api_server`
- **HTTP 而非 HTTPS**：Open WebUI → Hermes 为本地回路，HTTP 可；Open WebUI 对外是否启 HTTPS 取决于其自身配置
- **Open WebUI 端口**：`network_mode: host` 模式下，Open WebUI 默认监听其容器内端口（官方镜像为 8080），宿主机同端口可访问；若需改端口，须读镜像文档确认其暴露端口

## 已知注意事项

- Hermes `proxy start`（端口 8645）是面向 OAuth 提供商的 OpenAI 兼容代理，**不同于** `Platform.API_SERVER`（端口 8642）。Open WebUI 应接 8642。
- `docker logs open-webui` 查看容器启动日志
- 若 Hermes 8642 无监听，先确认 gateway 进程与平台配置：`hermes gateway status`
