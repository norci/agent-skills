---
name: skill-writing-guidance
description: skill 撰述之格式规范与雅言准则。凡创建、编辑、删除 skill，或调用 skill_manage 工具前，必先加载此 skill。
---

# Skill 撰述之则

## 总则

SKILL.md 是调用契约，不是系统文档

它只回答三个问题：**何时触发、怎么调、结果在哪**

内部如何实现 —— 无论 Python 脚本、OpenProse 服务、还是其他模块 —— LLM 读完对应文件自明，无需在此复述

凡撰 skill，文辞当雅，意约而赅。毋用白话，毋列细目，唯立纲领

## 诸戒

### 触发条件只入 description

- hermes skill frontmatter **无 `trigger` 字段**，写了亦无用
- `description` 同时承载本质描述与触发条件，LLM 在 system prompt 中即可判断是否加载
- ✅ `技术操作之规范。凡涉编码生成、系统维护、操作验证、技能管理，即当加载。`
- ❌ `规范技术操作之行为准则`（无触发条件，LLM 无法判断何时加载）
- **触发句式统一为：`凡[场景/动作]，即当加载。`** —— 此为机械可识别之最简触发模式，所有 skill description 宜采用此式

### 正文不提触发

- 正文**一字不提「触发条件」「适用场景」**
- 正文**不以「何时加载」「当……时触发」等标题开头**

### 正文大标题与 skill name 勿同

- 正文的一级标题（`#`）不应与 frontmatter 的 `name` 相同
- 应体现技能的定位或职能，而非直接重复名称

### SKILL.md 不抄内部实现

SKILL.md 写调用层知识，不写内部实现。实现细节在各模块文件里，LLM 读完自明

**谬** —— 把内部逻辑翻译成人话搬进 SKILL.md：
```markdown
## 执行流程
1. 首先调用 searxng 搜索实体，若返回结果少于 3 条则扩大搜索范围…
2. 然后对每个子问题执行两轮搜索，第一轮用宽泛关键词…
```

**正** —— 只写怎么调：
```markdown
## 执行
加载 open-prose skill，按其规程执行 `index.md`
```

以 OpenProse 写成之 skill，当声明加载 open-prose skill，`prose run` 是 LLM 在会话中直接解释执行之指令，毋须 shell 二进制

## 雅言之范

### 名（name）
- 仍用英文，以便系统辨识
- 例：`security-boundaries`

### 述（description）
- 当用雅言，一句话说「是什么」并含触发条件 —— **说本质，亦说何时用**
- ✅ `技术操作之规范。凡涉编码生成、系统维护、操作验证、技能管理，即当加载。`
- ✅ `凡需审视对话质量、检查回复合理性与对话伦理时，即当加载。`
- ❌ `规范技术操作之行为准则`（无触发条件）
- ❌ `对话心法`（过简，无触发）
- ❌ `规范代码生成、系统维护、查错验证…`（列了内部类别）

### 纲（正文）
- 用文言、半文半白
- 立纲领，不列细目
- 用 § # 等标目
- 忌：「## Core Principles」「### 1. User is Sovereign」

### 示范

**谬**：
```markdown
---
name: tech-ops
description: 编码生成、系统维护...之规范
trigger: 凡涉编码生成、系统维护...即当加载
---

# tech-ops

## 触发条件
凡涉以下任一类操作，加载此技能：
- 编码生成...

## 一、生成之律
...
```

**正**：
```markdown
---
name: tech-ops
description: 技术操作之规范。凡涉编码生成、系统维护、操作验证、技能管理，即当加载。
---

# 技术操作之律

## 一、生成之律
...
```

### 文言之诫
典雅文言之要：文辞华丽而不浮，简约而不陋；句式对仗工整，韵律和谐自然；遣词造句，皆有来历，非生造；表意准确，不因简而隐，不因繁而乱。辨伪典雅：凡遇堆砌虚辞、生造对仗、套话连篇，皆伪典雅，当删套话、留实质。

## 行文之律

- **尚简去繁**：删削冗余之展开、重复之譬喻、旁逸之附论。文以载意，不以多为胜
- **结构分明**：章节层级清晰，各守其界
- **示例从简**：示例仅示其要，毋铺陈为教程
- **正反对照**：以「正」「谬」示例示所倡所忌，一目了然
- **验证完备**：写入后自问 —— 此条必要否？典雅否？简练否？

## OpenProse Contract Markdown 之式

凡撰 OpenProse `*.prose.md` 服务或系统文件，当遵 v0.13.1 Contract Markdown 格式：

- 用 `### Requires` / `### Ensures` / `### Strategies` 作分区 header，**不用**裸 `requires:` / `ensures:` / `strategies:` 列表
- frontmatter 必有 `name` 与 `kind`（`service` | `system` | `gateway` | `test` | `pattern` | `responsibility`）
- `kind: system` 文件当有 `### Services` 节列出所组合的服务
- 可选节：`### Shape`、`### Runtime`、`### Errors`、`### Environment`、`### Memory`、`### Execution`

**谬**（旧式）：
```markdown
---
name: my-service
kind: service
---

requires:
- topic: research topic

ensures:
- report: findings
```

**正**（v0.13.1）：
```markdown
---
name: my-service
kind: service
---

### Requires

- `topic`: research topic

### Ensures

- `report`: findings
```

## 验符

撰毕当逐条核对诸戒，各戒标题即自检项
