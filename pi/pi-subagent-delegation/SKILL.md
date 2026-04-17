---
name: pi-subagent-delegation
description: 派分身的通道、角色、工具集与冲突规避。用 agents.run / agents.spawn 派分身时用。
---

# pi 分身

分身是独立 pi 进程，看不见本会话。任务描述须自带路径、目标、约束。

在 `fabric_exec` 里直接调，不是 `extensions.*`。

```ts
const r = await agents.run({ task: "...", readOnly: true, shell: "unconfined" });
```

关键入参：`task`（必填）、`agent`（`agents.definitions()` 里的名字）、`tools`、`readOnly`、`writableRoots`、`shell`、`schema`、`cwd`、`worktree`、`timeoutMs`、`queue`。

### 写权限与 shell 的冲突（最常见的错）

`readOnly: true` 拒 write/edit，**同时 bash/powershell 默认被拒**。要让只读分身跑 `git diff`，必须同时给 `shell: "unconfined"`。

- `unconfined` 不是沙箱，是真 shell。
- confined 模式不能用 native executor（CPython / node-process / bun-process）；要跑 python 得用 QuickJS 或 Monty。
- 多个分身并行用 `Promise.allSettled`；`Promise.all` 一个 reject 会中断整批。

## 写任务描述

三件事齐了再派，缺一件分身就会自己猜：

1. 目标：要什么产物（评审结论 / 文件路径清单 / 改好的代码）。
2. 位置：绝对路径，或仓库根加文件清单。
3. 约束：只读不改、别装依赖、别 commit。

反例（实际踩过）：开 `readOnly: true` 的分身，任务写「跑 git diff 看改动」——bash 被拒，分身死循环。

## 返回形状

`agents.run` 跑完才返回，形状是 `FabricAgentResult`：

```
{ id, runner, status, text, value?, error?, usage, turns, toolCalls, runnerSessionId? }
```

- `status` 是终态字符串；`text` 是分身最后那段话；配了 `schema` 才有 `value`（已校验的结构化数据）。
- 失败看 `error`，`text` 里通常还有半截产物。
- `agents.spawn` 只回 handle `{ id }`；`agents.wait({ id })` 回同样形状的 `FabricAgentResult`。`agents.status({ id })` 是运行中快照，不取值。

## 一次 fabric_exec 走完

派分身、等它跑完、判读结果、决定下一步，全在同一个程序里。**不许 spawn 一个 fabric_exec、wait 再来一个**：那是两次全量上下文重发，只为看一眼中间结果。

单发就用 `run`，它本身就是「启动 + 等完」：

```ts
try {
  const r = await agents.run({ task: "评审 /repo/src/queue.ts 的并发安全，报 file:line", readOnly: true });
  return { status: r.status, text: r.text, error: r.error };
} catch (e) {
  return { launchFailed: String(e) };
}
```

多发用 `Promise.allSettled`，一个失败不拖垮同批：

```ts
const [a, b] = await Promise.allSettled([
  agents.run({ task: "…", readOnly: true }),
  agents.run({ task: "…", readOnly: true, shell: "unconfined" }),
]);
const brief = (x: PromiseSettledResult<any>) =>
  x.status === "fulfilled"
    ? { status: x.value.status, text: x.value.text, error: x.value.error }
    : { rejected: String(x.reason) };
return { a: brief(a), b: brief(b) };
```

要在程序里继续判读、续派下一步，就 `await` 之后当场判：

```ts
const r = await agents.run({ task: "列出 /repo/src 下所有 TODO，给 file:line", readOnly: true });
if (r.status !== "completed" || !r.text.includes("file:")) return { retryNeeded: r.error ?? "no findings" };
const r2 = await agents.run({ task: `按这些位置写修复计划：\n${r.text}`, readOnly: true });
return { plan: r2.text };
```

`spawn` 只在两种情况下用：要 `queue: true` 排出并发上限，或要 `residency: "durable"` 让它活过本会话。其余一律 `run`。

## 取结果

- `text` 是分身的原话，别整段塞回主上下文；在程序里筛出结论、file:line、失败原因再 return。
- 配 `schema` 时读 `result.value`，不要从 `text` 里抠 JSON。
