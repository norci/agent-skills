---
name: pi-subagent-delegation
description: 派分身的通道、角色与结果取法。用 acp_delegate 派分身时用。
---

# pi 分身

分身是独立 pi 进程，看不见本会话。任务描述须自带路径、目标、约束。

## 通道

`acp_delegate` 在 `codemode` 里直接调。角色只有五个，各自带固定工具集：

| 角色 | 用途 | 工具 |
| --- | --- | --- |
| `reviewer` | 审代码，报 file:line | 只读 |
| `researcher` | 摸清陌生代码 | 只读 |
| `planner` | 出分步计划 | 只读 |
| `oracle` | 答问题、给建议 | 只读 |
| `worker` | 改代码 | read + edit + write |

## 派发

`async` 默认 true，立即回 `runId`，跑完自动把结果文件路径通知进会话。要当场拿结果就 `async: false` 阻塞，或 `acp_delegate_wait({ runId, timeout })`（上限 300 秒）。

多个分身并行：`Promise.allSettled` 一次派完，一个失败不拖垮同批。

```ts
const [a, b] = await Promise.allSettled([
  tools.acp_delegate({ agent: 'reviewer', task: '评审 /repo/src/queue.ts 的并发安全，报 file:line' }),
  tools.acp_delegate({ agent: 'researcher', task: '查清 /repo/src/auth 里 token 刷新的调用链，给 file:line' }),
]);
return [a, b].map((x) => (x.status === 'fulfilled' ? x.value : `rejected: ${x.reason}`)).join('\n');
```

失败或取消的运行保留输出文件，可用 `resumeFrom: '<runId>'` 接着跑，不必重派。

## 写任务描述

三件事齐了再派，缺一件分身就会自己猜：

1. 目标：要什么产物（评审结论 / 文件路径清单 / 改好的代码）。
2. 位置：绝对路径，或仓库根加文件清单。
3. 约束：只读不改、别装依赖、别 commit。

反例（实际踩过）：任务写「跑 git diff 看改动」但没说明要改文件——只读角色跑不了 git 之外的写操作，分身原地打转。

## 取结果

- 完整结果落在文件里，路径由工具返回。`read` 那个文件，只把结论、file:line、失败原因搬回主上下文。
- 判定失败看通知里的 ⚠️ 与错误摘录；失败的分身不产出可用结果。
