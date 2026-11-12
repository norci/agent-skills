---
name: gitee
description: Gitee issue 与 PR 的形参、正文体例与判据。建或改 issue、PR 时用。
---

# Gitee issue 与 PR

issue 记现象，PR 带修法，常在同一轮里做。实测报错原文见 `references/pitfalls.md`。

一段流程一个程序：取仓库、写单、回读断言是一条链，链末断言，不拆成多次调用，也不靠人读输出判断。

## 形参

| 形参 | 取值 |
| --- | --- |
| `owner` | 空间地址：个人、组织或企业路径 |
| `repo` | 仓库路径，不带 `owner` |
| `number` | PR 为整数，issue 为字符串（如 `IKSQJK`），两者互不通用 |
| `labels` | 逗号分隔，须已存在于仓库，名字 2–20 字，不确定就不传 |
| `head` | `branch` 或 `path_with_namespace:branch`，跨仓库写 `owner:branch` |
| `body` | Markdown；长文经变量传入，不内联进调用 |

取 `owner`、`repo`：读 `git remote get-url origin`，从末尾两段切出，`https://gitee.com/owner/repo.git` 与 `git@gitee.com:owner/repo.git` 都成立；向 fork 提时改用对应 remote 名，不是 `origin`。

## 建 issue

```mermaid
graph TD
    A["git remote get-url origin"] -->|"owner, repo"| B["create_issue(title, body, labels?)"]
    B -->|"number, state"| C["get_repo_issue_detail(number)"]
    C -->|"number, title, state"| D{"与所写相符且 state 为 open"}
    D -->|"是"| E["输出 number"]
    D -->|"否"| F["断言失败, 不输出"]
```

正文一次写全，不靠事后 `update_issue` 补。体例（缺一节就别写这节，不写空标题）：

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

## 改 issue

```mermaid
graph TD
    A["输入 number 与新 title"] -->|"body / labels / state 可选"| B["update_issue(number, title, body?, labels?, state?)"]
    B -->|"state 为 closed"| C["关单"]
    B -->|"state 略去"| D["正文与标签已改, 单仍开"]
```

`title` 必传，即使只改标签、正文或状态。列表查询的形参为 `state`、`sort`、`direction`、`per_page`；大仓用 `state` 为 open，取全部会超出单次输出上限。

## 建 PR

```mermaid
graph TD
    A["body 首行 关联 issue: #编号"] -->|"不传 issue 形参, 它会顶掉 PR 标题"| B["git rev-parse HEAD"]
    B -->|"head"| C["git push -u origin 分支"]
    C --> D["git ls-remote --heads origin refs/heads/分支"]
    D -->|"输出含 head"| E["create_pull(title, head, base, body)"]
    E -->|"number, html_url, head.sha"| F["list_repo_pulls(state=open, direction=desc)"]
    F -->|"列表"| G{"head.sha 等于 head 且 title 相符"}
    G -->|"是"| H["输出 html_url"]
    G -->|"否"| I["断言失败, 不输出"]
```

分支存在与否只有一个判据：`git ls-remote --heads origin`。`--dry-run` 不落远端 ref；`compare_branches_tags` 比的是 tag；PR 合入后远端 ref 常被删，本地跟踪分支仍会列它。

## 改 PR

正文只写不读：`update_pull` 与单条详情都不回 `body`，页面匿名访问被挡。判据落在写入前的本地断言与写入后的 ref 断言上，各一次。

```mermaid
graph TD
    A["body 首行 关联 issue: #编号"] --> B["update_pull(number, title, body)"]
    B -->|"number 为整数"| C["git rev-parse HEAD"]
    C -->|"head"| D["git ls-remote --heads origin refs/heads/分支"]
    D -->|"输出含 head"| E["list_repo_pulls(state=open, direction=desc)"]
    E -->|"列表"| F{"number 相符且 head.sha 等于 head 且 title 相符"}
    F -->|"是"| G["改动已落"]
    F -->|"否"| H["断言失败"]
```

正文对不对，靠写之前核一次；写完不读，因为服务端不回 `body`。为「正文写进去没有」另起通道不产生新读数，且拿占位正文探回执会覆盖刚写好的正文。
