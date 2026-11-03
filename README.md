# agent-skills

自建 skill 仓库，按 harness 分三棵子树。两套 harness 都递归扫描目录，故靠「给谁链接哪一棵」隔离，不靠命名约定。

| 树 | 内容 | 谁加载 |
|---|---|---|
| `common/` | 与 harness 无关的技能（金融数据、devops、重构、git、安全边界） | pi 与 hermes 都加载 |
| `hermes/` | 只用 Hermes 工具的技能（`memory`、`skill_manage`、`tts`、`lisp` MCP、Hermes 本体运维） | 仅 hermes |
| `pi/` | 只用 pi 工具的技能（`fabric_exec`、`crw`、`serena`、`lightpanda`） | 仅 pi |

## 装配

```text
~/.pi/agent/skills/common -> ~/code/agent-skills/common
~/.pi/agent/skills/pi     -> ~/code/agent-skills/pi
```

```yaml
# ~/.hermes/config.yaml
skills:
  external_dirs:
  - ~/code/agent-skills/common
  - ~/code/agent-skills/hermes
  - ~/.agents/skills
```

## 判定

写进哪棵树，看技能里出现的工具名：`memory`、`skill_manage`、`text_to_speech`、`~/.hermes/*` 属 hermes；`fabric_exec`、`extensions.*`、`crw_*`、`serena`、`lightpanda` 属 pi；两者都不提则为 common。

目录内可再分类（`devops/`、`finance/`、`workflow/`），分类只影响阅读，不影响加载。
