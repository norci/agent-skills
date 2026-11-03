# Agent-facing Python wrapper pattern

## 背景

当 agent 需调用某个 Python package 且随后继续写分析代码时，厚 CLI dispatcher 会压扁表达力。较善之形，是以可 import 的 helper module 封住副作用边界，让 agent 只写最少业务调用代码。

## 模式

- helper module 提供少数函数，如 `call(...)`、`list_apis(...)`、`info(...)`
- helper 负责认证、连接、login/logout、stdout/stderr 静默、异常检查、结果归一化
- agent 直接 `import` helper，生成业务查询、筛选、聚合、输出
- CLI 入口若保留，只作 smoke test、手工探查、兼容门面

## 适用

- 上游 API 多且参数差异大
- agent 后续需要在 Python 内继续解析、计算、汇总
- 资源生命周期或副作用容易遗漏

## 不适用

- 用户只需固定命令式查询
- 输出无需再加工
- 工具面向非 Python 调用者
