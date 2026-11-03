# akcli — AKShare 取数壳

## 开发决策记录

- **黑名单策略**：`blocked.json` 是配置入口，`auto_ban.py` 是引擎。配置与代码分离，改规则时只改 JSON，不动代码。即使 JSON 值含义不完美或格式不一致，也优先于此文件。