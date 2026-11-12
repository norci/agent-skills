---
name: gitee
description: Gitee issue 与 PR 的形参、正文体例与判据。建或改 issue、PR 时用。
---

# Gitee issue 与 PR

实测报错原文见 `references/pitfalls.md`。

一条流程写成一个程序：取仓库、写单、回读核对串成一条链，链末比字段是否相符，链中不逐段确认，不靠人读输出判断。

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

正文一次写全。体例（缺一节就别写这节，不写空标题）：

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

`title` 必传。列表查询的形参为 `state`、`sort`、`direction`、`per_page`；大仓传 `state: open`。

## 建 PR

```mermaid
graph TD
    A["body 首行 关联 issue: #编号"] -->|"不传 issue 形参"| B["git rev-parse HEAD"]
    B -->|"head"| C["git push -u origin 分支"]
    C --> D["git ls-remote --heads origin refs/heads/分支"]
    D -->|"输出含 head"| E["create_pull(title, head, base, body)"]
    E -->|"number, html_url, head.sha"| F["list_repo_pulls(state=open, direction=desc)"]
    F -->|"列表"| G{"head.sha 等于 head 且 title 相符"}
    G -->|"是"| H["输出 html_url"]
    G -->|"否"| I["断言失败, 不输出"]
```

分支存在与否只认 `git ls-remote --heads origin` 的输出，不用 `--dry-run`、`compare_branches_tags`、本地跟踪分支。判据比内容（sha、分支名），不比真值。

## 改 PR

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

正文写前核一次，写完不读，不为正文另起通道。
