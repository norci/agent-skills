# 实测原文

## 编号传错

PR 工具传字符串或浮点报 `must be an integer, not a float`；issue 工具收字符串。

## 输出超限

`list_repo_pulls({ state: "all" })` 在大仓回 20099 字符（约 5759 token），截断后不是合法 JSON。同仓 `state: "open"` 回 1067 字符。

## 抓页面

取 `https://gitee.com/<owner>/<repo>/pulls/<n>` 回 HTTP 403（`您的访问受限`）。

## 标签不存在

有的空间静默忽略，有的报错。

## update_issue 缺 title

schema 报错。

## issue 形参顶掉 PR 标题

`create_pull({ owner, repo, title: "A", issue: "IKSG90", head, base })` 建出的 PR 标题是 IKSG90 的标题，`title` 被弃用。

## 分支不在远端

`400 (code: 400, details: 源分支 <branch> 不存在)`

## 空输出

空 stdout 被归一为 `"(no output)"`。

## 合入后源分支已删

未 `git fetch --prune` 时本地跟踪分支仍在，`git branch -vv` 仍列它。
