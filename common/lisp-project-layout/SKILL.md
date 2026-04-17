---
name: lisp-project-layout
description: 在 ~/code 建 Lisp/Quicklisp 项目、挂进 local-projects 时用。
---

# Lisp 项目目录之律

用户以 `~/code/` 作为所有源码仓库（含 `git clone` 目标）之根目录。

- **源码**：`~/code/<project>/`
- **Quicklisp local-projects**：以 symlink 指向 `~/code/<project>/`，而非相反
- **Quicklisp 本体**：`~/quicklisp/`（上游惯例，不动）
- **严禁**：在 `~/` 下散落 `.lisp`、`.sexp`、`setup.lisp`、`asdf.lisp` 等临时文件；快速安装后若不净，立刻清理
