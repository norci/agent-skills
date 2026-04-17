---
name: git-ops
description: Git 与远端操作准则，远端归属按配置而非惯例推断。改远端、推送、定分支归属时用。
---

# Git 操作之律

## 前置之律

凡操作远程仓库，必先查已有状态：`git remote -v`、`gh auth status`、`gh api` 确认 fork 是否存在。fork、force push、改 remote、删除分支等不可逆操作，尤应先确认

## Remote 之律

- 不擅自添加、删除、修改 remote URL
- SSH remote 需确认 key 已配；HTTPS remote 需确认 token 可用
- 若 remote 缺失或 URL 有误，告之用户，请旨后行
- 本机 GitHub 直连受阻时，可用 gh-proxy 作 rewrite：
  `git config --global url."https://v6.gh-proxy.org/https://github.com/".insteadOf "https://github.com/"`。此 rewrite 仅限于 `https://github.com/`，其他 CDN 不受影响

## Fork 之律

- `gh repo fork` 前先查 fork 是否已存在
- fork 至个人账号后，本地 remote 名与上游区分：`origin` 指上游，个人 remote 另取名
- 若仓库 remote 经代理改写，`gh repo view` 可能不识别当前目录所属 GitHub 仓库；此时对 `gh repo fork/view` 传显式 `owner/repo`，并先读 `gh repo fork --help`。部分 `gh` 版本在传 `<repository>` 时不支持 `--remote`；当分两步行之：先 `gh repo fork owner/repo`，再本地 `git remote add <fork-remote> <fork-url>`。

## 分支命名

遵目标项目 CONTRIBUTING 之规。无特殊规范时：

- `feat/description` —— 新功能
- `fix/description` —— 修复
- `docs/description` —— 文档
- `refactor/description` —— 重构
- `test/description` —— 测试

## Commit 格式

遵目标项目规范。无特殊要求时，默认 Conventional Commits：`type(scope): description`

## PR 描述

- 只述 what / why / how to test
- 不提本地私有内容：自建 skill、私有配置、本地路径、会话过程
- 一 PR 一变更，保持聚焦

## Push 之律

- 先确认 remote URL 类型与认证状态
- force push 前确认无他人基于该分支工作

## 合入后收尾

- Gitee 按 squash 合入时合并提交单亲（`git rev-list --parents -n 1 <merge>` 只有一个父），分支 tip 不是它的祖先，`git merge-base --is-ancestor <tip> <merge>` 返假 —— 不能据此判「未合并」。
- 判据改用树比对：`git diff --stat <tip> <merge>` 无输出即内容一致，可删分支。
- 删分支与删 worktree 同序：先 `git worktree remove <path>`，再 `git branch -D <branch>`；分支仍在 worktree 里检出时删不动。

## 验证

- 代码变更：确认模块可加载
- schema 变更：确认 schema 对象 import 无报错
- 描述性变更：手动验证即可
