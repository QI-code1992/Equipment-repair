# 外部开发基线输入登记

本文件登记本次纳入项目正式开发要求的外部材料。原文件保留在项目外部桌面目录；以下 SHA-256 用于追溯输入版本。纳入后，以本仓库编号 Stage 文档和 workflow 台账为执行依据。

| 文件 | SHA-256 | 纳入范围 |
|---|---|---|
| `今日对接结论.md` | `0af47a65a9902c773eae92cc231de9df6e220a116d5c6d743c0a238aa2de78f7` | 健康分、SLA、风险、停用冻结、数据源排除 |
| `开发基线说明.md` | `ee4cebea2eb88f77cce7ec1aadcc16fb16042c70bca8816fb7c80147489e514c` | 唯一依据、历史材料禁用、原型修订和开发前置 |
| `开发交付入口.md` | `be4ad84de0b44c28203b01748fa6467ba7d2c75bedd9a24431641761b1ab6846` | 本期开发/不开发范围、运行和验收入口 |
| `AI_RAGFLOW_LANGGRAPH_SPEC.md` | `91e3a0026e6fecbadbc5f169c1f72f4e5248fb34ded4aecf2212ad2869eda77b` | AI 技术架构、边界、API、工具白名单、安全和 AI 验收 |

## Canonical mapping

- Requirements: `01-requirements/PRD.md`, `01-requirements/SPEC.md`, `01-requirements/ACCEPTANCE_CRITERIA.md`
- Interaction/prototype: `02-product-interaction-design/`, `03-ui-prototype/`
- Architecture: `04-architecture-plan/SYSTEM_ARCHITECTURE.md`, `API_SPEC.md`, `DATA_MODEL.md`, `IMPLEMENTATION_PLAN.md`
- Testing/release: `06-testing/TEST_PLAN.md`, `08-release-handoff/DEPLOYMENT_CHECKLIST.md`

外部材料不得直接作为开发人员的第二套依据；如与 canonical 文档冲突，必须进入 `workflow/CHANGE_REQUESTS.md` 并完成基线澄清。
