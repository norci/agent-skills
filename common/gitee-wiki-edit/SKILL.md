---
name: gitee-wiki-edit
description: 改 Gitee 仓库 wiki 时用。
---

# Gitee Wiki 之道

## 本质

Gitee wiki 即仓库旁之独立 Git 仓库 `https://gitee.com/<owner>/<repo>.wiki.git`，每页为一个 Markdown 文件，默认分支实测为 `master`。Gitee OpenAPI v5 无 wiki 端点，gitee MCP 亦无 wiki 工具，唯一通道是 git。

## 认证

token 须为仓库 owner 或协作者之私人令牌。私有仓库匿名不可读，故每次操作皆须带 token，并先清空本机 credential helper（本机 helper 指向 GitHub，会掩盖真实认证状态）：

| 要点 | 命令片段 |
|:---|:---|
| 清空 helper | `git -c credential.helper=` |
| 注入 token | `-c http.extraheader="Authorization: Basic $(printf 'oauth2:%s' "$GITEE_TOKEN" | base64 -w0)"` |
| 禁交互 | `GIT_TERMINAL_PROMPT=0` |

token 只经环境变量 `GITEE_TOKEN` 传入，不写入命令历史与文件。

## 调用

```bash
scripts/gitee-wiki.sh <owner/repo> <本地目录> clone
scripts/gitee-wiki.sh <owner/repo> <本地目录> pull
scripts/gitee-wiki.sh <owner/repo> <本地目录> push "docs: 更新某页"
```

clone 后改 `.md` 文件，再 push；push 一并完成 add、commit 与推送。

## 判据

| 判据 | 通过 | 不通过 |
|:---|:---|:---|
| 读权 | `git ls-remote` 有 ref 输出 | `could not read Username` |
| 写权 | `push --dry-run` 报 `[new branch]` 或 `up-to-date` | 同上 |

## 陷阱

- 首次 clone 成功不等于匿名可读：全局 helper 可能代供凭据。须清空 helper 后不带 token 复测，应失败。
- `push --dry-run` 不落远端 ref，改完用 `git ls-remote` 复核提交号。
- 网页 `gitee.com/<owner>/<repo>/wikis/*` 无登录返回 403，不可作读写判据。
