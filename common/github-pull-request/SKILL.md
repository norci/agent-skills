---
name: github-pull-request
description: 在 GitHub 上开 PR 前：GitHub 交付 PR 的命令与字段。
---

# GitHub PR 命令

## 硬规则

- PR 正文用英文书写，包括标题、章节名与图内标签。
- 推送到 fork 之前，先把分支变基到 `origin` 的 `master`/`main`，再推送；变基后远端不可快进，用 `git push --force-with-lease=refs/heads/<branch>:<旧 sha>` 推。

## 判 fork 与父仓库

```
gh api repos/<owner>/<repo> --jq '[.fork, .parent.full_name]'
```

`.fork=true` 且有父仓库时目标是父仓库，`.fork=false` 时目标是本仓库。

## 查权限

```
gh repo view <target-owner>/<repo> --json viewerPermission
```

WRITE、MAINTAIN、ADMIN 可直接推该仓库；READ、TRIAGE 不可。

## 仓库归属与放置

克隆放 `~/code/<repo>`。

```
gh api user --jq .login
gh api repos/<owner>/<repo> --jq '.owner.login, .fork'
```

owner 与当前账号不同时，这个仓库不是你的：不直接推它的分支。fork 后把工作推 fork，向父仓库开 PR。

```
gh repo fork <owner>/<repo> --clone=false
git clone https://github.com/<your-user>/<repo>.git ~/code/<repo>
git -C ~/code/<repo> remote add upstream https://github.com/<owner>/<repo>.git
git -C ~/code/<repo> checkout -b <fix-branch>
```

改完本地验证通过再提交；推送与 PR 见「经 fork 交付」。

## 经 fork 交付

1. 确认 fork 存在：`gh repo view <your-user>/<repo> --json name`。
2. 推分支到 fork：`git push <fork-url> <branch>:<branch>`。
3. 建 PR，三点写全：

```
gh pr create --repo <upstream-owner>/<repo> --base <base-branch> --head <fork-owner>:<branch>
```

`--head` 的 `<fork-owner>` 只接受用户名，不接受组织。省略 `--head` 时 gh 按当前目录的 remote 推断，推不上去才提示是否 fork，结果不由你控制。

`isFork=true` 的仓库上省略 `--repo` 时，gh 拿当前目录的 remote 当目标，PR 落进 fork 自己的 base 分支。同名分支在 fork 与父仓库是两个东西。

## 复核

```
gh pr view <n> --json url,isCrossRepository,headRepositoryOwner,baseRefName
```

`isCrossRepository` 为 `true` 说明 head 来自另一个仓库，`url` 里的 owner 就是 base 所属仓库。`gh pr view` 没有 `baseRepository` 字段，写上会报 unknown field。

## 推送通路

- SSH 经 `ProxyCommand` 转发时，可能在 banner exchange 处超时；此时报错是网络，不是权限。
- HTTPS 推送用 gh 的凭据助手：

```
git -c credential.helper='!gh auth git-credential' push https://github.com/<owner>/<repo>.git <branch>:<branch>
```

- 报 `Head sha can't be blank`、`No commits between ...`、`Head ref must be a branch` 时，先核推送是否真的成功。
