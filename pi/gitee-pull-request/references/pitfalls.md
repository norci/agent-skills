# Gitee PR 之坑

## issue 形参顶掉标题

`create_pull({owner, repo, title: "A", issue: "IKSG90", head, base})` 建出的 PR 标题不是 `A`，是 IKSG90 这个 issue 的标题；`title` 被静默弃用。

两条出路：

- 不传 `issue`，正文首行写 `关联 issue: #IKSG90`（推荐，标题可控）。
- 建完立刻 `update_pull` 把 `title` 改回；实测改得动。

## body 读不回

`create_pull`、`update_pull`、`get_pull_detail`、`list_repo_pulls` 的返回里都没有 `body` 字段。因此：

- 正文是否落盘**只能开网页看**，MCP 侧无法核验。
- 与用户交代时写「属推断」，并给出 `https://gitee.com/<owner>/<repo>/pulls/<number>` 供其核验。

## 网页抓不到

`extensions.mcp__crw__crw_scrape` 抓 `https://gitee.com/x/y/pulls/n` 返回 HTTP 403（`您的访问受限`，Gitee 挡匿名）。scrape 不能作核验手段，也不要多试。

## 工具名与发现

- pi 中调用形如 `extensions.mcp__gitee__create_pull`。
- `tools.describe` 的形参是 `ref`（单数）；传 `discover` 或 `@tool:` 前缀会报错。
- 同名工具在 codemode 脚本里另有 `mcp.gitee.<tool>` 形，本文只用 `extensions.*`。

## number 的类型

- PR：整数 `3`；传字符串或浮点报错（schema 注「must be an integer, not a float」）。
- issue：字符串 `"IKSG90"`。

## 提交前的前置

`create_pull` 不代推分支。分支不在远端时先 `git push -u origin <branch>`，并以 `git ls-remote --heads origin refs/heads/<branch>` 见 sha 为判据（`--dry-run` 不落远端 ref，不算数）。
