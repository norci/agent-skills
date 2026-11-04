---
name: gitee-pull-request
description: 在 Gitee 上建 pull request 并核对。凡要把分支提 PR、改 PR 标题或正文、查已有 PR 状态时，即当加载。
---

# Gitee PR

一气呵成的写法：先推分支，再在一个 `fabric_exec` 程序里建 PR、改标题与正文、复核结果。

## 建 PR

推分支与建 PR 同在一个程序里，推送结果按 sha 比对断言，不靠输出真值判断：

```ts
const branch = "fix/xxx", base = "main";
const head = (await pi.bash({ cmd: "git rev-parse HEAD", settle: true })).output!.trim();
await pi.bash({ cmd: `git push -u origin ${branch}`, settle: true });
const seen = (await pi.bash({ cmd: `git ls-remote --heads origin refs/heads/${branch}`, settle: true })).output!;
if (!seen.includes(head)) throw new Error(`分支未落远端: ${seen}`);

const pull = await extensions.mcp__gitee__create_pull({ owner, repo, title, head: branch, base, body });
// 返回 {number, html_url, ...}; number 是整数
```

空 stdout 由 `pi.bash` 归一为字符串 `"(no output)"`，故判据取 `includes(head)`，不取 `seen.trim()` 的真假；见 `references/pitfalls.md` 之「空输出读作 (no output)」。

`head` 形如 `branch` 或 `path_with_namespace:branch`，方括号照抄:

```ts
const cross = await extensions.mcp__gitee__create_pull({
  owner, repo,
  head: `${owner}:${branch}`,   // 跨仓库时用此形
  base: "main",
  title: "t",
  body,
});
```

`body` 是 Markdown；首行写 `关联 issue: #IKSG90` 即把 PR 挂到 issue，见 `references/pitfalls.md` 之「issue 形参顶标题」。

## 改标题或正文

```ts
await extensions.mcp__gitee__update_pull({
  owner, repo,
  number: pull.number,          // 整数，非字符串
  title: "新的标题",
  body,                          // body 与 title 同传即一次改完
});
```

## 复核

```ts
const listed = await extensions.mcp__gitee__list_repo_pulls({ owner, repo, state: "open", direction: "desc" });
const sha_now = (await pi.bash({ cmd: "git rev-parse HEAD", settle: true })).output?.trim();
// 判据：某条 PR 的 head.sha === sha_now 且 title 对得上
```

单条详情的形参同 `update_pull`：`{ owner, repo, number }`，`number` 必须是整数。

## 参数来源

查 schema 用 `tools.describe`，形参名是 `ref`（单数），值不带 `@tool:` 前缀：

```ts
const d = await tools.describe({ ref: "mcp__gitee__create_pull" });
```

本文件所述行为的内情与核验判据见 `references/pitfalls.md`。
