---
name: gitee
description: Gitee issue 与 PR 的形参名、返回信封与正文体例。建或改 issue、PR 时用。
---

# Gitee issue 与 PR

issue 记现象，PR 带修法，常在同一轮里做。实测报错原文见 `references/pitfalls.md`。

一段流程一个程序：推分支、建 PR、回读核对是一条链，链末用 `throw` 断言，不拆成三次
fabric_exec，也不靠人读输出判断。下面两段可直接照抄，只换 payloads 与分支名。

## 建 issue

```ts
// payloads: issue_body
const url = (await pi.bash({ cmd: "git remote get-url origin", settle: true })).output!.trim();
const [, owner, repo] = url.replace(/\.git$/, "").match(/[:/]([^/:]+)\/([^/]+)$/)!;
// https://gitee.com/owner/repo.git 与 git@gitee.com:owner/repo.git 都解出 owner, repo
// 向 fork 提时改用对应 remote 名，不是 origin

const created = await extensions.mcp__gitee__create_issue({
  owner,                 // 空间地址：个人、组织或企业路径
  repo,                  // 仓库路径，不带 owner
  title: "一句话说清是什么坏了",
  body: π.issue_body,    // Markdown；长文一律走 payloads
  labels: "bug",         // 逗号分隔；须已存在于仓库，名字 2–20 字，不确定就不传
});
const issue = JSON.parse(created.text);   // { id, number: "IKSQJK", title, state, body, ... }
// number 是字符串（IKSQJK），与 PR 的整数编号互不通用

const detail: any = await extensions.mcp__gitee__get_repo_issue_detail({
  owner, repo, number: issue.number,
});
const got = JSON.parse(detail.text);
if (got.number !== issue.number || got.title !== "一句话说清是什么坏了" || got.state !== "open")
  throw new Error(`issue 回读不符: ${JSON.stringify({ number: got.number, title: got.title, state: got.state })}`);
```

正文一次写全，不靠事后 `update_*` 补。体例（缺一节就别写这节，不写空标题）：

```markdown
## 现象
命令、输出原文、复现步骤。

## 成因
表格：文件:行 · 那一行的内容。

## 代价
后果，写成「改这里会牵连 X」。

## 修法
打算改哪一层、改哪几处。

## 验证
判据命令与预期。
```

改单与关单走 `update_issue`，`title` 必传（即使只改标签、正文或状态），`state: "closed"` 即关单：

```ts
await extensions.mcp__gitee__update_issue({
  owner, repo, number: issue.number, title: "新标题", body: π.issue_body, labels: "bug", state: "closed",
});

await extensions.mcp__gitee__list_repo_issues({
  owner, repo, state: "open", sort: "created", direction: "desc", per_page: 20,
});
```

## 建 PR

```ts
// payloads: pr_body（正文首行写 `关联 issue: #IKSQJK`，不传 issue 形参 —— 它会顶掉 PR 标题）
const url = (await pi.bash({ cmd: "git remote get-url origin", settle: true })).output!.trim();
const [, owner, repo] = url.replace(/\.git$/, "").match(/[:/]([^/:]+)\/([^/]+)$/)!;
const branch = "fix/xxx", base = "main", title = "fix: 一句话说清改了什么";

const head = (await pi.bash({ cmd: "git rev-parse HEAD", settle: true })).output!.trim();
await pi.bash({ cmd: `git push -u origin ${branch}`, settle: true });
const seen = (await pi.bash({ cmd: `git ls-remote --heads origin refs/heads/${branch}`, settle: true })).output!;
if (!seen.includes(head)) throw new Error(`分支未落远端: ${seen}`);

const created = await extensions.mcp__gitee__create_pull({
  owner, repo, title, head: branch, base, body: π.pr_body,
});
const pull = JSON.parse(created.text);   // html_url、head.sha 皆在此；number 是整数

const listed = await extensions.mcp__gitee__list_repo_pulls({ owner, repo, state: "open", direction: "desc" });
const mine = JSON.parse(listed.text).find((item: any) => item.head?.sha === head);
if (!mine || mine.title !== title) throw new Error(`PR 回读不符: ${JSON.stringify(mine)}`);
print(pull.html_url);
```

`head` 形如 `branch` 或 `path_with_namespace:branch`，跨仓库时写 `${owner}:${branch}`。

分支存在与否只有一个判据：`git ls-remote --heads origin`。`--dry-run` 不落远端 ref；
`compare_branches_tags` 比的是 tag；PR 合入后远端 ref 常被删，本地跟踪分支仍会列它。

## 返回信封与 schema

所有 gitee MCP 工具回 `{content, text, details, isError, structuredContent, source}`，
`details` 只有 `{server, tool}`，数据在 `text`（JSON 字符串）：单条 `JSON.parse(created.text)`，
列表得数组。读 `created.number` 这类顶层字段只会得到 `undefined`。

形参以 schema 为准，`ref` 是单数、值不带 `@tool:` 前缀：

```ts
const d = await tools.describe({ ref: "mcp__gitee__create_pull" });
```

单条详情的形参同 `update_pull`，`number` 必须是整数；它与列表两处都不回 `body`。
