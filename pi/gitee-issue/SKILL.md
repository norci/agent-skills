---
name: gitee-issue
description: 在 Gitee 上建 issue、改标题正文、加标签、关联 PR 并核对。凡要报缺陷或需求、把 issue 挂到 PR、或查已有 issue 状态时，即当加载。
---

# Gitee issue

一气呵成：一个 `fabric_exec` 程序里从 git remote 取 owner/repo、建 issue、回读核对、把编号交给后续步骤。正文从 payloads 进，代码体只写 `π.issue_body`。

## 取 owner 与 repo

不写死仓库名。仓库归属由当前工作树的 origin 决定，每次现取：

```ts
const url = (await pi.bash({ cmd: "git remote get-url origin", settle: true })).output!.trim();
const [, owner, repo] = url.replace(/\.git$/, "").match(/[:/]([^/:]+)\/([^/]+)$/)!;
// https://gitee.com/owner/repo.git  → owner, repo
// git@gitee.com:owner/repo.git     → owner, repo
```

判据：`owner` 与 `repo` 都非空，且 `url` 的 host 是 gitee.com。要向 fork 提 issue 时，改用对应 remote 名（`git remote get-url <remote>`），不是 `origin`。

## 建 issue

```ts
const created = await extensions.mcp__gitee__create_issue({
  owner,                 // 空间地址：个人、组织或企业路径
  repo,                  // 仓库路径，不带 owner
  title: "一句话说清是什么坏了",
  body: π.issue_body,    // Markdown；长文一律走 payloads
  labels: "bug",         // 逗号分隔；标签须已存在于仓库，名字 2–20 字
});
const issue = JSON.parse(created.text);   // { id, number: "IKSQJK", title, state, body, ... }
// number 是字符串，形如 IKSQJK / I5ABCD; 顶层是信封, 数据在 .text
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

## 回读核对

`create_issue` 返回的 `body` 是入参回显，不证明落盘一致。要核验就另取：

```ts
const detail: any = await extensions.mcp__gitee__get_repo_issue_detail({
  owner, repo, number: issue.number,   // 字符串，非整数
});
const got = JSON.parse(detail.text);   // 含 body, 与 create 之回显可比
```

判据：`number`、`title`、`state === "open"` 三项对得上；`body` 长度与首行亦可比。

## 改标题、正文、标签、状态

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

`title` 是必填项：只改标签或状态时，把原标题原样再传一遍。

## 列 issue

```ts
await extensions.mcp__gitee__list_repo_issues({
  owner, repo, state: "open", sort: "created", direction: "desc", per_page: 20,
});
```

## 挂到 PR

PR 侧不传 `issue` 形参（它会顶掉 PR 标题），改为在 PR 正文首行写：

```markdown
关联 issue: #IKSQJK
```

## 参数来源

查 schema 用 `tools.describe`，形参名是 `ref`（单数），值不带 `@tool:` 前缀：

```ts
const d = await tools.describe({ ref: "mcp__gitee__create_issue" });
```

内情与核验判据见 `references/pitfalls.md`。
