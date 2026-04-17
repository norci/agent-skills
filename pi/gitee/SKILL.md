---
name: gitee
description: Gitee issue 与 PR 的形参名、返回信封与正文体例。建或改 issue、PR 时用。
---

# Gitee issue 与 PR

issue 记现象，PR 带修法，常在同一轮里做。两件事共用取仓库坐标、读返回信封、查 schema 三段。内情与核验判据见 `references/pitfalls.md`。

## 取 owner 与 repo

不写死仓库名。仓库归属由当前工作树的 origin 决定，每次现取：

```ts
const url = (await pi.bash({ cmd: "git remote get-url origin", settle: true })).output!.trim();
const [, owner, repo] = url.replace(/\.git$/, "").match(/[:/]([^/:]+)\/([^/]+)$/)!;
// https://gitee.com/owner/repo.git  → owner, repo
// git@gitee.com:owner/repo.git     → owner, repo
```

判据：`owner` 与 `repo` 都非空，且 `url` 的 host 是 gitee.com。向 fork 提 issue 或 PR 时，改用对应 remote 名（`git remote get-url <remote>`），不是 `origin`。

## 返回信封

所有 gitee MCP 工具回 `{content, text, details, isError, structuredContent, source}`，`details` 只有 `{server, tool}`，数据在 `text`（JSON 字符串）。单条取 `JSON.parse(created.text)`，列表取 `JSON.parse(listed.text)` 得数组。读 `created.number` 这类顶层字段只会得到 `undefined`。

## 参数来源

查 schema 用 `tools.describe`，形参名是 `ref`（单数），值不带 `@tool:` 前缀：

```ts
const d = await tools.describe({ ref: "mcp__gitee__create_pull" });
```

## Issue

### 建 issue

```ts
const created = await extensions.mcp__gitee__create_issue({
  owner,                 // 空间地址：个人、组织或企业路径
  repo,                  // 仓库路径，不带 owner
  title: "一句话说清是什么坏了",
  body: π.issue_body,    // Markdown；长文一律走 payloads
  labels: "bug",         // 逗号分隔；标签须已存在于仓库，名字 2–20 字
});
const issue = JSON.parse(created.text);   // { id, number: "IKSQJK", title, state, body, ... }
// number 是字符串，形如 IKSQJK / I5ABCD
```

正文体例（缺一节就别写这节，不写空标题）：

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

### 回读核对

`create_issue` 返回的 `body` 是入参回显，不证明落盘一致。要核验就另取：

```ts
const detail: any = await extensions.mcp__gitee__get_repo_issue_detail({
  owner, repo, number: issue.number,   // 字符串，非整数
});
const got = JSON.parse(detail.text);   // 含 body, 与 create 之回显可比
```

判据：`number`、`title`、`state === "open"` 三项对得上；`body` 长度与首行亦可比。

### 改标题、正文、标签、状态

```ts
await extensions.mcp__gitee__update_issue({
  owner, repo,
  number: "IKSQJK",      // 字符串
  title: "新标题",        // 必传，即使不改
  body: π.issue_body,    // 与 title 同传即一次改完
  labels: "bug",
  state: "closed",       // 关单也走这里
});
```

### 列 issue

```ts
await extensions.mcp__gitee__list_repo_issues({
  owner, repo, state: "open", sort: "created", direction: "desc", per_page: 20,
});
```

## PR

### 建 PR

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

`head` 形如 `branch` 或 `path_with_namespace:branch`，跨仓库时写 `${owner}:${branch}`。

### 挂 issue

`create_pull` 的 `issue` 形参会顶掉 PR 标题（标题被换成该 issue 的标题）。改为在 PR 正文首行写：

```markdown
关联 issue: #IKSQJK
```

### 改标题或正文

```ts
await extensions.mcp__gitee__update_pull({
  owner, repo,
  number: pull.number,          // 整数，非字符串
  title: "新的标题",
  body,                          // body 与 title 同传即一次改完
});
```

### 复核

```ts
const listed = await extensions.mcp__gitee__list_repo_pulls({ owner, repo, state: "open", direction: "desc" });
const pulls = JSON.parse(listed.text);   // 数组；state:"all" 超输出上限会被截断
const sha_now = (await pi.bash({ cmd: "git rev-parse HEAD", settle: true })).output?.trim();
// 判据：某条 pull.head.sha === sha_now 且 title 对得上
```

单条详情的形参同 `update_pull`：`{ owner, repo, number }`，`number` 必须是整数。其 JSON 无 `body`。

### 核验正文

MCP 侧读不回正文（`create_pull` / `update_pull` / `get_pull_detail` / `list_repo_pulls` 皆无 `body`），走 Gitee api v5，凭证取环境变量 `GITEE_TOKEN`：

```ts
const file = "/tmp/pr.json";
await pi.bash({
  cmd: `curl -s -o ${file} -H "Authorization: token $GITEE_TOKEN" https://gitee.com/api/v5/repos/${owner}/${repo}/pulls/${pull.number}`,
  settle: true,
});
const got = JSON.parse(await pi.read({ path: file }));
// got.body 即正文, 首行应为「关联 issue: #IKSQJK」
```

内联 `curl`（不带 `-o`）会被 context-mode 钩子拦下，必须落盘再读；token 只用 `$GITEE_TOKEN`，不写进命令正文、不回显。
