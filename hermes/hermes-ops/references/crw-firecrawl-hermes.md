# CRW 作 Hermes `web_extract` 本机 Firecrawl 后端

## 适用

用户要以 `https://github.com/us/crw` 自托管抓取服务，供 Hermes `web_extract` 使用。CRW 暴露 Firecrawl 兼容 `/v1/scrape`，故 Hermes 侧应配置 `firecrawl` backend，而非新造 `crw` backend 名。

## Compose 部署要点

- 建议放在既有 dockerfiles 树下独立目录，如 `code/dockerfiles/crw/docker-compose.yaml`，便于后续 `docker compose pull && docker compose up -d` 更新镜像。
- 默认先起单容器 CRW，JS 渲染器（LightPanda/Chrome）可先放入 `profiles: [js]`，避免首部署因多镜像 pull 过慢阻塞；待镜像拉齐后，再把 renderer 移出 profile，使其随 CRW 默认启动。
- 最小环境：
  - `CRW_SERVER__HOST=0.0.0.0`
  - `CRW_SERVER__PORT=3000`
  - 若无 JS renderer：`CRW_RENDERER__MODE=none`
- LightPanda 接入环境：
  - `CRW_RENDERER__MODE=auto`
  - `CRW_RENDERER__LIGHTPANDA__WS_URL=ws://lightpanda:9222/`
  - `crw.depends_on.lightpanda.condition=service_started`
- `lightpanda/browser` 镜像以 `tini` 为 entrypoint；compose 中 `command` 宜写成 shell 字符串：`lightpanda serve --host 0.0.0.0 --port 9222 --log-level info`，勿改成 YAML list 以免触发 tini 直接 exec 子命令的坑。
- CRW 服务端口只绑本机：`127.0.0.1:3000:3000`。
- 若用户明确要求 Hermes 或其他本机/局域网组件直接连 LightPanda CDP，可为 `lightpanda` 加端口映射：`0.0.0.0:9222:9222`。这是 CDP 控制面外暴，须有用户明旨；改后用 `ss -ltnp '( sport = :9222 )'` 与 `http://127.0.0.1:9222/json/version` 验证。
- LightPanda 的 `/json/version` 可能回报 `webSocketDebuggerUrl: ws://0.0.0.0:9222/`；局域网客户端通常应改用宿主机实际 IP/域名连接，而非字面 `0.0.0.0`。

## Hermes 配置

```bash
hermes config set web.extract_backend firecrawl
```

在当前 profile 的 `.env` 中设置：

```bash
FIRECRAWL_API_URL=http://127.0.0.1:3000
```

自托管 CRW 默认无需 `FIRECRAWL_API_KEY`；若服务端后来启用认证，再按其要求补 key。

## 验证顺序

1. `docker compose config` 校验 compose。
2. `docker compose up -d` 起服务；若 LightPanda 尚在 profile 内，先用 `docker compose --profile js pull lightpanda` 拉镜像，长 pull 用后台 `notify_on_complete=true`，不要用短前台 timeout。
3. `curl -fsS http://127.0.0.1:3000/health` 应返回 `status: ok`。
4. 直调 `/v1/scrape`，确认能取回 `data.markdown`。
5. 若已接 LightPanda，检查 CRW 日志含：
   - `Renderer mode: Auto`
   - `Lightpanda CDP: ws://lightpanda:9222/`
   - `JS renderers in fallback order: ["lightpanda"]`
   并在直调 `/v1/scrape` 的 `metadata.renderedWith` 看到 `lightpanda`。
6. `hermes config check` 确认 `FIRECRAWL_API_URL` 被识别。
7. 重启 Hermes Agent 后调用 `web_extract` 做端到端验证。

## 198.18/代理 DNS 陷阱

若本机 DNS/透明代理把公网域解析到 `198.18.0.0/15`、`100.64.0.0/10` 等网段，Hermes 的 SSRF 预检会在进入 CRW 前拦截，报：

```text
Blocked: URL targets a private or internal network address
```

用 `getent ahosts <host>` 或 `tools.url_safety.is_safe_url()` 证实后，按 Hermes 源码支持的开关临时放行此环境：

```bash
hermes config set security.allow_private_urls true
```

注意：该开关在进程内有缓存，须重启 Hermes Agent 后生效；云元数据地址（如 `169.254.169.254`）仍应被强制封禁。若用户后来撤去 fake-ip/代理 DNS，使公网域恢复真实公网解析，应主动复默认安全态：

```bash
hermes config set security.allow_private_urls false
```
