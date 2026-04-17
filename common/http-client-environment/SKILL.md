---
name: http-client-environment
description: 查 HTTP 去向或代理来源前：确认 HTTP 客户端实际连到哪里、代理从哪取。
---

# 客户端实际连到哪里

## 判据是连接目标，不是配置

包装底层的连接函数，跑一次真实请求，收下它收到的 `(host port)`。这个目标是请求实际去的地方；客户端自己的配置、环境变量、日志都不构成判据。

```lisp
(let ((orig (symbol-function 'usocket:socket-connect)))
  (setf (symbol-function 'usocket:socket-connect)
        (lambda (&rest args)
          (push (list (first args) (second args)) *targets*)
          (apply orig args))))
```

目标是服务自身端口，才算请求直连。否则先解决被谁接走，再谈服务端行为。

## 代理取值发生在载入时

`dexador` 在载入时把代理读进 `dexador.backend.usocket::*default-proxy*`，值是代理 URL。此后进程里改环境变量不改变它：`getenv` 已回 NIL，请求仍走代理。

判据：把该变量置 NIL 后重跑同一请求，连接目标从代理端口变成服务自身端口。清环境变量必须发生在载入之前，晚一步都无效。

## 本地服务被代理接管

代理对指向本机的请求回 `400`，客户端把这个状态当服务端的应答，错误文本指向服务，看起来像服务拒绝。

判据：同一请求绕过代理后返回正常状态与正常体。`NO_PROXY` 里写了本地地址，不代表客户端遵守；证据仍取连接目标。
