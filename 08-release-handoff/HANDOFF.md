# 项目文档与原型交接

本文件记录当前工作区面向同事接手的候选交接快照。它不是生产发布，也不代表任何 Stage Gate 已获批准。

- 交接版本：`handoff/candidate-v20260714-01`
- 交接分支：`agent/formal-stage-gate-migration`
- 仓库：[QI-code1992/Equipment-repair](https://github.com/QI-code1992/Equipment-repair)
- 提交 SHA：以 annotated tag `handoff/candidate-v20260714-01` 指向的提交为准

## 包含内容

- `00-opportunity` 至 `08-release-handoff` 的阶段文档
- `workflow` 工作流状态、资产基线、外部输入和变更台账
- `03-ui-prototype` 静态 HTML/CSS/JavaScript 原型
- `06-testing/tests` 原型静态回归检查

## 拉取方式

```bash
git clone https://github.com/QI-code1992/Equipment-repair.git
cd Equipment-repair
git fetch --tags origin
git checkout handoff/candidate-v20260714-01
```

如需继续开发，请从交接分支创建新分支，不要移动该不可变标签。

## 当前边界

- 生产实现尚未开始，原型不等同于生产接口、权限、安全或验收测试。
- Stage 0–8 文档均为候选资料，尚无阶段审批结论。
- 交接前已完成静态测试、JavaScript 语法检查和 `git diff --check`；不包含浏览器视觉验收或部署验证。
