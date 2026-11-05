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

const created = await extensions.mcp__gitee__create_pull({ owner, repo, title, head: branch, base, body });
const pull = JSON.parse(created.text);   // number 是整数, html_url、head.sha 皆在此
```

MCP 工具一律回信封 `{content, text, details, isError, structuredContent, source}`，PR 的 JSON 在 `text` 里（字符串），顶层没有 `number` / `html_url` —— 取 `created.number` 得 `undefined`。见 `references/pitfalls.md` 之「返回信封」。

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
const pulls = JSON.parse(listed.text);   // 数组, 元素同上
const sha_now = (await pi.bash({ cmd: "git rev-parse HEAD", settle: true })).output?.trim();
// 判据：某条 pull.head.sha === sha_now 且 title 对得上
```

单条详情的形参同 `update_pull`：`{ owner, repo, number }`，`number` 必须是整数。其 JSON 无 `body`，正文核验见下节。

## 核验正文

MCP 侧读不回正文（`create_pull` / `update_pull` / `get_pull_detail` / `list_repo_pulls` 皆无 `body`），走 Gitee api v5，凭证取环境变量 `GITEE_TOKEN`：

```ts
const file = "/tmp/pr.json";
await pi.bash({
  cmd: `curl -s -o ${file} -H "Authorization: token $GITEE_TOKEN" https://gitee.com/api/v5/repos/${owner}/${repo}/pulls/${pull.number}`,
  settle: true,
});
const got = JSON.parse(await pi.read({ path: file }));
// got.body 即正文, 首行应为「关联 issue: #IKSSCB」
```

内联 `curl`（不带 `-o`）会被 context-mode 钩子拦下，必须落盘再读；token 只用 `$GITEE_TOKEN`，不写进命令正文、不回显。

## 参数来源

查 schema 用 `tools.describe`，形参名是 `ref`（单数），值不带 `@tool:` 前缀：

```ts
const d = await tools.describe({ ref: "mcp__gitee__create_pull" });
```

本文件所述行为的内情与核验判据见 `references/pitfalls.md`。
