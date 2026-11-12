# 判据的由来

SKILL.md 只留形状与判据。这里是实测报错原文与数字，规则本身变了才回来改这里。

## 编号传错的报错

PR 工具传字符串或浮点报 `must be an integer, not a float`；issue 工具收字符串。

## 输出超限即非 JSON

`list_repo_pulls({ state: "all" })` 在大仓回 20099 字符（约 5759 token），超宿主输出上限，`text` 前被插入 `Warning: truncated output (original token count: 5759)`，`JSON.parse` 报 `unexpected token: 'Warning'`，栈顶在 `<input>:1:1`，不在 gitee 调用。剥前缀救不回来（尾也断了，报 `expecting '}'）。同仓 `state: "open"` 只 1067 字符。

## 抓页面被挡

抓取工具取 `https://gitee.com/<owner>/<repo>/pulls/<n>` 回 HTTP 403（`您的访问受限`，Gitee 挡匿名）。

## 标签不存在时两种表现

有的空间静默忽略、有的报错。

## update_issue 缺 title 的报错

只改标签、正文或状态时也传 `title`，否则 schema 报错。

## issue 形参顶掉 PR 标题

`create_pull({ owner, repo, title: "A", issue: "IKSG90", head, base })` 建出的 PR 标题是 IKSG90 的标题，`title` 被静默弃用；建完立刻 `update_pull` 改得动。

## 分支不在远端的报错

`400 (code: 400, details: 源分支 <branch> 不存在)` —— 不是权限，不是命名。

## 空输出读作 (no output)

命令执行器把空 stdout 归一为 `"(no output)"`，判空永不为假 —— 判据要比内容（sha、分支名），不能比真值。

## 合入后源分支已被删

未 `git fetch --prune` 时本地跟踪分支仍在、`git branch -vv` 仍列它；拿它再建 PR 得同一条 400。
