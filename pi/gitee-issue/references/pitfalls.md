# Gitee issue 之坑

## 仓库坐标现取，不写死

`owner` 与 `repo` 由 `git remote get-url origin` 解出。把仓库名写进技能、写进示例代码，换仓库即失效，也容易把别人的仓库当成自己的。

向 fork 提 issue 时用对应 remote 的 URL，不一定是 `origin`；提交前先 `git remote -v` 看清哪一个是目标仓库。

## 编号是字符串

issue 的 `number` 形如 `"IKSQJK"`，PR 的 `number` 是整数 `3`。issue 工具收字符串，PR 工具收整数，互不通用。

## 正文核验

`create_issue` 返回的 `body` 是入参回显，不证明服务端落盘一致。要核验就再调 `get_repo_issue_detail({owner, repo, number})`，读 `text` 或 `structuredContent`。

## 标签须预先存在

`labels` 收逗号分隔的名字，长度 2–20、非特殊字符。仓库里没有该标签时，有的空间静默忽略、有的报错。不确定就不传，或先 `list_repo_issues` 看一条已有 issue 的 `labels`。

## update_issue 的 title 必填

只改标签、正文或状态时也要传 `title`，否则 schema 报错。把当前标题原样传回即可。

## PR 关联 issue 的两条路

- `create_pull({issue: "IKSQJK", ...})`：会顶掉 PR 标题，改用 issue 的标题。
- PR 正文首行写 `关联 issue: #IKSQJK`（推荐，标题可控）。

## 工具名与发现

- 调用形如 `extensions.mcp__gitee__create_issue`。
- `tools.describe` 的形参是 `ref`（单数），值不带 `@tool:` 前缀。
- 返回是信封 `{content, text, details, isError, structuredContent, source}`，数据在 `text`（JSON 字符串），取 `JSON.parse(text)`。

## 长正文走 payloads

正文含中文长句、反引号、`${}`、换行时，写进代码体会解析失败。放进顶层 payloads，代码体只写 `π.issue_body`。
