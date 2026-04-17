---
name: git-ops
description: 规范 Git 与 GitHub 操作之行为准则。凡涉 clone、fork、PR、push、remote 操作，即当加载。
---

# Git 操作之律

## 前置之律

凡操作远程仓库，必先查已有状态：`git remote -v`、`gh auth status`、`gh api` 确认 fork 是否存在。fork、force push、改 remote、删除分支等不可逆操作，尤应先确认

## Remote 之律

- 不擅自添加、删除、修改 remote URL
- SSH remote 需确认 key 已配；HTTPS remote 需确认 token 可用
- 若 remote 缺失或 URL 有误，告之用户，请旨后行

## Fork 之律

- `gh repo fork` 前先查 fork 是否已存在
- fork 至个人账号后，本地 remote 名与上游区分：`origin` 指上游，个人 remote 另取名

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

## 验证

- 代码变更：确认模块可加载
- schema 变更：确认 schema 对象 import 无报错
- 描述性变更：手动验证即可
