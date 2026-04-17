# Gitee issue 与 PR 之坑

## 仓库坐标现取，不写死

`owner` 与 `repo` 由 `git remote get-url origin` 解出。把仓库名写进技能、写进示例代码，换仓库即失效，也容易把别人的仓库当成自己的。

向 fork 提 issue 或 PR 时用对应 remote 的 URL，不一定是 `origin`；提交前先 `git remote -v` 看清哪一个是目标仓库。

## 编号的类型两边不同

- issue：`number` 是字符串 `"IKSG90"`，issue 工具收字符串。
- PR：`number` 是整数 `3`，传字符串或浮点报错（schema 注「must be an integer, not a float」）。

两种编号互不通用，把 issue 的字符串塞进 PR 工具即报错。

## 返回信封

所有 gitee MCP 工具都回 `{content, text, details, isError, structuredContent, source}`，其中 `details` 只有 `{server, tool}`，数据在 `text`（JSON 字符串）：

- 单条：`JSON.parse(created.text)` → `{number, html_url, head: {sha}, ...}`。
- 列表：`JSON.parse(listed.text)` → 数组。

读 `created.number`、`detail.body` 这类顶层字段只会得到 `undefined`，随后按 undefined 走复核分支，白耗往返。

### 输出超限即非 JSON

`list_repo_pulls({state: "all"})` 在大仓回 20099 字符（约 5759 token），超宿主输出上限，`text` 前被插入 `Warning: truncated output (original token count: 5759)`，JSON 在中途截断，`JSON.parse` 报 `unexpected token: 'Warning'`。栈顶是解析处（`<input>:1:1`），不在 gitee 调用，别当取数失败重试。

剥前缀救不回来（尾也断了，报 `expecting '}'`）。收窄查询：同仓 `state: "open"` 只 1067 字符；再不够用 `head`、`per_page`、`page` 分页。

## 正文核验

- issue：`create_issue` 返回的 `body` 是入参回显，不证明服务端落盘一致。要核验就再调 `get_repo_issue_detail({owner, repo, number})`，读 `text` 或 `structuredContent`。
- PR：`create_pull`、`update_pull`、`get_pull_detail`、`list_repo_pulls` 的 JSON 里都没有 `body` 字段，回显只有元数据。核验走 Gitee api v5：

```bash
curl -s -o /tmp/pr.json -H "Authorization: token $GITEE_TOKEN" \
  https://gitee.com/api/v5/repos/<owner>/<repo>/pulls/<number>
```

返回的 `body` 即正文。两条限制：内联 `curl` 被 context-mode 钩子拦（报「Use context-mode MCP tools」），必须带 `-o` 落盘再读文件；token 取环境变量，不写进命令正文、不回显。

## 正文一次传齐

建 issue 或 PR 时 `body` 一次写全，不靠事后 `update_*` 补。PR 回显无 `body`，补没补上只能再查一次 api —— 一次没写对就多两次往返。

正文含中文长句、反引号、`${}`、换行时，写进代码体会解析失败。放进顶层 payloads，代码体只写 `π.issue_body`。

## 标签须预先存在

`labels` 收逗号分隔的名字，长度 2–20、非特殊字符。仓库里没有该标签时，有的空间静默忽略、有的报错。不确定就不传，或先 `list_repo_issues` 看一条已有 issue 的 `labels`。

## update_issue 的 title 必填

只改标签、正文或状态时也要传 `title`，否则 schema 报错。把当前标题原样传回即可。

## issue 形参顶掉 PR 标题

`create_pull({owner, repo, title: "A", issue: "IKSG90", head, base})` 建出的 PR 标题不是 `A`，是 IKSG90 这个 issue 的标题；`title` 被静默弃用。

两条出路：

- 不传 `issue`，正文首行写 `关联 issue: #IKSG90`（推荐，标题可控）。
- 建完立刻 `update_pull` 把 `title` 改回；实测改得动。

## 提交前的前置

`create_pull` 不代推分支。分支不在远端时报 `400 (code: 400, details: 源分支 <branch> 不存在)` —— 不是权限，不是命名。先跑 `git ls-remote --heads origin refs/heads/<branch>`，无输出即漏了 push（`--dry-run` 不落远端 ref，不算数）。

## 空输出读作 (no output)

`pi.bash` 把空 stdout 归一为字符串 `"(no output)"`，`output.trim()` 永不为假。判据要比内容（sha、分支名），不能比真值 —— 否则「没推上去」与「已推上去」同判，push 整段被跳过。

## 合入后源分支可能已被删

PR 合入后远端 ref 常被删。未 `git fetch --prune` 时本地跟踪分支仍在、`git branch -vv` 仍列它；拿它再建 PR 得同一条 400。先 `git ls-remote --heads origin` 看远端还剩哪些分支。

## 诊断别乱试接口

`compare_branches_tags` 比的是 tag，不答「分支在不在」；拿它诊断 400 只多一次 404。分支存在与否的判据只有 `git ls-remote --heads origin`。

## 网页抓不到

`extensions.mcp__crw__crw_scrape` 抓 `https://gitee.com/x/y/pulls/n` 返回 HTTP 403（`您的访问受限`，Gitee 挡匿名）。scrape 不能作核验手段，也不要多试。

## 工具名与发现

- pi 中调用形如 `extensions.mcp__gitee__create_issue`、`extensions.mcp__gitee__create_pull`。
- `tools.describe` 的形参是 `ref`（单数）；传 `discover` 或 `@tool:` 前缀会报错。
- 同名工具在 codemode 脚本里另有 `mcp.gitee.<tool>` 形，本文只用 `extensions.*`。
