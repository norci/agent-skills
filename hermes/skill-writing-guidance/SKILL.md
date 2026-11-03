---
name: skill-writing-guidance
description: skill 撰述之格式规范与雅言准则。凡创建、编辑、删除 SKILL.md 文件，或调用 skill_manage 工具前，即当加载。
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

以 OpenProse 成之 skill，当声明加载 open-prose skill，`prose run` 是 LLM 在会话中直接解释执行之指令，毋须 shell 二进制

### 契约内容不二处

当 skill 使用 OpenProse 架构（`index.md` + `services/*.prose.md`）时，契约内容（`### Requires` / `### Ensures` / `### Strategies`）已由 prose 文件承载，SKILL.md 只须引用路径，不得复引或改编。复引导致两处须同步变更，且读者困惑该听谁的。

### 契约边界：SKILL.md 非 Prose 契约之容器

OpenProse 架构有二层契约：

| 层级 | 文件 | 职责 | 读者 |
|------|------|------|------|
| 使用契约 | SKILL.md | 何时触发（description）、加载哪些 Prose 文件、参数列表、执行注意事项 | 决定是否加载此 skill 的 Agent |
| 服务契约 | `index.md`（系统定义）、`services/*.prose.md`（服务定义） | Requires、Ensures、Strategies——即产出什么、质量如何、路径在哪 | 已加载 skill 并进入执行阶段的 Agent |

**重要原则**：输出质量规范（正文风格、分章结构、文件命名、输出路径、引用格式）等属于**服务契约**（`### Ensures`/`### Strategies`），不属于 SKILL.md。SKILL.md 只需说「产出格式见 index.md 与 services/synthesizer.prose.md」，不应内嵌契约正文。

**理由**：
1. SKILL.md 的读者是「决定是否加载的 Agent」，契约的读者是「执行中的 Agent」—— 两读者关注不同
2. 契约正文嵌入 SKILL.md 后，变更时须同步两处，且让 Agent 困惑该听谁的
3. 契约文件自有其格式（Contract Markdown 的 `### Requires/Ensures/Strategies`），SKILL.md 的 Markdown 格式与之不匹配

**注意**：此原则**不否定**「行为规范必入正文，勿托于 references」—— 对于**非 OpenProse 架构**的 skill，输出规范仍在 SKILL.md 正文中。OpenProse 技能的特殊之处在于输出规范已有专门的契约文件承载（`.prose.md` 的 `### Strategies`），SKILL.md 应指向而非复制。

**SKILL.md 不列出 prose.md 路径**：OpenProse 引擎讀取 `index.md` 時，`### Services` 已聲明所有服務，引擎自會加載對應 prose.md。SKILL.md 若再列出「見 `services/xxx.prose.md`」之類指針，實為冗餘——Agent 依 open-prose 流程自會讀到，毋須 SKILL.md 越俎代庖。若 SKILL.md 需要強制 Agent 走 open-prose VM 路徑（如禁止手動編排 delegate_task），應在 SKILL.md 正文中寫明執行路徑與禁令，而非列出 prose.md 路徑。

**反例**（deep-research SKILL.md 越界实录）：
```
### Pitfalls（实测发现）
- ⚠️⚠️ 核心禁令：不得绕过 open-prose VM 直接调用 subagent ...
- 根本问题：LLM 编排 LLM 不可靠 ...
- searcher 超时 ...
- evidence.md 可能缺失 sources.md ...
- 证据层隐蔽扭曲（详见 `services/searcher.prose.md` 自检清单）...
```
上述内容分属三类越界：
1. `核心禁令` 是对编排层的**方法约束**，属 `index.md` / `prose.md` 契约范围，不是 SKILL.md 的触发层知识
2. `根本问题`、`searcher 超时`、`evidence.md 缺失` 是**内部实现与运行时经验**，`index.md` 的 `### Strategies` 已承载部分，其余应归 `docs/` 备忘
3. `证据层隐蔽扭曲` 已完整写入 `services/searcher.prose.md` 的 `### Strategies`，SKILL.md 只需一句指针：「searcher 契约见 `services/searcher.prose.md`」

### 诸界之诫——跨域污染之防

#### 症候

通用 skill（如「一切会话之伦理」之类）常被渗入仅适用于特定场景的规范。典型症状：
- 研究设计方法论（框架偏见、频率偏见）出现于通用答复伦理中
- searcher 阶段的证据层扭曲手法出现于通用心术中
- 特定技能的执行细节被写入「所有会话都应遵守」的条目

本质原因是：**在通用 skill 中追加条目时，自洽性感知被覆盖**——「这条很重要」≈「这条应放在最重要的通用 skill 中」，而非「这条是否约束一切会话」。

#### 检测方法

逐条检查通用 skill 中的每条规则：

1. **替换测试**：将此规则的适用主语从「一切会话」替换为「特定场景（如 deep-research 的证据搜集阶段）」。若替换后语境依然合理，则说明该规则可能应属于特定场景 skill
2. **边界问询**：问自己「这条规则被触发时，是否同时需要加载该领域 skill 才能完整理解？」若是，说明它属于领域 skill，不应脱离领域 skill 单独生存
3. **删除测试**：若从通用 skill 中移除本条，通用 skill 是否仍保持完整自洽？若是，说明本条是外来插入的

#### 修复方法

- 将属于领域 skill 的条目迁出，整合到对应领域的服务契约（`.prose.md` 的 `### Strategies`）中
- 通用 skill 内仅保留本条引用的指针（如「证据层扭曲自检清单见 `deep-research` skill 的 searcher 契约」）——但前提是该指针确实需要跨 skill 引用
- **更佳**：不保留指针。通用 skill 只说「当执行特定任务时，加载对应 skill 以获取领域契约」，不留空洞引用

#### 内容净化之界

**通用化（genericize）原则适用所有知识载体**，不只限于 prose.md：

| 知识载体 | 是否应清除特定案例术语 | 原因 |
|----------|------------------------|------|
| SKILL.md | ✅ 正文中不应出现测试名、具体案例名 | 触发条件与行为规范应领域无关 |
| prose.md (服务契约) | ✅（已有规则） | 合同不得特化 |
| references/ 文件 | ✅ | 供参考，但对契约无增量约束；整合完毕后应删除 |
| memory | ✅ | 案例测试是解题过程，memory 只需保留谜底（通用原则） |
| user profile | ✅ | 用户画像应基于稳定的行为模式，而非单一测试事件 |
| session DB (历史记录) | ❌ | 历史不可改——但不应被 memory/skill 引用 |

### 测试示例日期须用近期

SKILL.md 中若含带日期的示例（如涨停股池 `date=20260317`），该日期可能已过期，致测试时返回空数据。当用近期有数据之日，或标注「日期须为近期交易日」。

### prose.md 契约自洽性原则

prose.md 是自洽的契约，不依赖外部参考文件来补全行为规则。以下四条为本轮实战教训：

**一、语义整合，非机械复制**

当从 `references/` 文件迁移内容到 prose.md 时，必须**语义编辑**（semantic edit），不是机械复制粘贴。提炼行为约束的**本质规则**，去掉案例上下文（如特例名称、具体领域词汇等）。反例：直接将 reference 中带案例的段落整段粘贴到 `critic.prose.md` 的 Strategies——用户纠正：「不要直接把 reference 的内容 copy to prose.md，必须要语义上的编辑」。

**二、通用化（genericize）**

prose.md 是合同（contract），不是领域说明书。合同内禁止出现特定案例术语（如具体领域术语、不适、健康人群分类）。所有规则必须以**领域无关的通用形式**表述。反例：`critic` 策略中出现「扫描报告中描述具体体验的段落」「如定义「害」=「器质性病变」，回避「即时感受」」——用户纠正：「要从 prose.md 中去掉任何与具体案例描述有关的特化术语。要作为完全通用的 contract，不要特化为特定领域术语」。正确做法：将具体术语改为"某个具体体验"，将"不适/疼痛"改为"具体经验描述"，将"敏感人群"改为"边缘案例"。

**三、references/ 用完即删**

凡 `references/` 中文件已被语义化整合到 prose.md 中的，该文件应立即删除。不保留「以备参考」的冗余文件。references/ 不是契约持久存储——只有**尚未整合**或**真正独立有价值**的参考才存在。用户要求：「references 目录内的文件越来越多，真的有必要吗？必须精简掉」。

**四、流程图等文档放 `docs/`**

流程图、架构图等辅助理解性文档，属于文档（documentation）而非契约（contract）。应存放于 skill 根目录下的 `docs/` 目录，不放在 `references/` 或 inline 在 prose.md 中。用户确认：「流程图是文档，可以换个位置放」。

### 自建 skill 之归属

凡用户手写之自建 skill，当置于 `~/code/agent-skills/` 下三分树之一（`common/`、`hermes/`、`pi/`，判据见仓库 README），经 `skills.external_dirs` 加载。不可直接写入 `~/.hermes/skills/`——后者由 `hermes update` 管理，会被覆写。

Agent 以 `skill_manage create` 写入 `~/.hermes/skills/` 者，为 Agent 所制，非用户自建，**不可迁移**至 `~/code/agent-skills/`。

若误将自建 skill 写入 `~/.hermes/skills/`，当用 `mv` 整目录迁移而非 `rm + 重写`——后者费 token 且失文件历史。

### 判断 skill 来源之法

`~/.hermes/skills/` 中已有之 skill，按来源分四类：

| 来源 | 判定依据 | 能否迁移 |
|------|---------|---------|
| 官方 bundled | 列于 `~/.hermes/skills/.bundled_manifest` | 否 |
| Hub 安装 | 列于 `~/.hermes/skills/.hub/lock.json` 之 `installed` 下 | 否 |
| Curator 合并(consolidated umbrella) | 属 `consolidated/` 类，不在以上两文件中 | 否（Hermes 管家自动创建） |
| Agent 或用户创建 | 以上皆否，且 SKILL.md 首行 `---` 间有 frontmatter | 仅用户手写方可迁移 |

具体操作：`read_file` 读 `.bundled_manifest`（每行 name:hash），再用 `execute_code` 读 `.hub/lock.json`。两清单之外的 skill，查其分类是否 `consolidated/` 以排除 curator 产物。用户手写者方可迁至 `~/code/agent-skills/`。

### 行为规范必入正文，勿托于 references

**凡影响输出质量、格式、风格、用户偏好的行为规范，必须直接写入 SKILL.md 正文。** 不可将其托付于 `references/` 目录中的外部文件，不可依赖 LLM「自行加载」参考文件。

**理由**：LLM 加载 skill 时优先阅读 SKILL.md 正文。`references/` 中的文件是可选深度阅读，非强制——若核心行为规范仅存于 reference，LLM 跳过时即丧失约束。

**辨正**：

| 位置 | 适合什么 | 不适合什么 |
|------|----------|------------|
| SKILL.md 正文 | 输出质量规范、文件结构强制规则、分章存储要求、正文风格约束、用户明确设定的偏好 | 冗长的执行记录、实战教训详解、示例对比大段 |
| references/ | 执行记录、实战详情、示例对照、扩展读本 | 行为规范本身——SKILL.md 中应先写入规范，references 仅作补充说明或示例展开 |

**操作规则**：
1. 先问：「这条规则被 LLM 跳过会怎样？」—— 若后果是输出质量下降、格式错误、用户纠正，则必须入正文
2. 正文中先写规范要点（条文化），references 再写示例展开和实战详情
3. SKILL.md 末尾的「相关参考」列表仅作为指向补充资料的索引，不得以此替代正文中的规范

### 迁移泛化之律（Migration Sanitization）

**当跨文件迁移内容时（如将一个 skill 的段落移至另一个 skill/prose.md），必须在同一轮操作中将原文中的具体案例名称替换为通用概念。不可「先迁移、后泛化」分两轮。**
- 具体案例名称（如某次测试名、领域特例、产品名）是「谜面」—— 它们属于被验证的上下文，而非可复用的规则
- 迁移到目标技能后，读者（未来 Agent）不再有原案例的上下文，保留具体名字会使其误以为该规则仅适用于特定案例
- 若分两轮执行（先迁移内容，后等用户指出再泛化），则让用户为 Agent 的遗漏买单

**反例**（本轮实战教训）：
```
第一阶段：将某通用 skill 中的「问题框架偏见」「频率偏见」移至
         deep-research 的 decomposer/searcher 契约
         → 正确迁移了位置，但内容中保留了具体测试案例名称
第二阶段：用户指出后，才做第二轮泛化替换
         → 用户承受了两轮成本，暴露了「迁移时未同步泛化」的遗漏
```

**正例**：迁移时直接在目标文件中写「某具体体验」「目标变量」「某场景」，而非先写具体术语，等下一轮再改。

### 归类之律——skill 架构原则

SKILL.md 应遵守单一职责：一个技能只覆盖**一类场景**，不做跨类聚合。

- **通用唯一**：通用会话伦理集中为一份通用 skill，凡所有会话皆遵行之规范，悉入此文
- **各建专技**：凡属特定场景（研究、开发、运维、写作等），各建独立 skill 承载其规程，其内容不含通用伦理
- **裁断之戒**：凡增条目于通用 skill 之前，必自问：「此条是否约束一切会话？」若否，当建新 skill 限制加载范围，切勿以通用之律杂覆特定场景细则
- **跨领域迁移信号**：若发现某 skill 的一段内容实际上更适合另一 skill（如通用伦理中混入了研究方法论），应直接迁移并在迁移泛化之律指导下完成跨域修复

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
- 用 # 等标目

### 文言之诫
典雅文言之要：文辞华丽而不浮，简约而不陋；句式对仗工整，韵律和谐自然；遣词造句，皆有来历，非生造；表意准确，不因简而隐，不因繁而乱

## 行文之律

- **尚简去繁**：删削冗余之展开、重复之譬喻、旁逸之附论。文以载意，不以多为胜
- **结构分明**：章节层级清晰，各守其界
- **示例从简**：示例仅示其要，毋铺陈为教程
- **验证完备**：写入后自问 —— 此条必要否？典雅否？简练否？

## 验符

撰毕当逐条核对诸戒，各戒标题即自检项