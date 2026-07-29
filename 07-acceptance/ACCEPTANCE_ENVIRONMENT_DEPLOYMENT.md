# Stage 7 隔离验收环境部署

## 状态与目的

- 状态：候选方案，等待项目负责人确认；未部署。
- 验收候选：`89fbd2129169fb6ece42094b17907885637f3c48`。
- 目的：为项目负责人提供隔离的实际产品环境，用于逐项判断验收标准；这不是生产发布。
- 禁止事项：不得使用生产数据、生产凭据、公开互联网入口或 `main`；不得把环境启动、页面可访问或单项通过表述为最终验收通过。
- 采用方案：已批准的单机 Windows Docker Desktop/WSL2 方案，平台 PostgreSQL 17 与独立 RAGFlow Docker Compose 栈通过受控本机连接协作；Nginx 仅绑定回环 HTTPS。外部 ECS、FRP 和 PostgreSQL 16 环境不在本次验收范围内。

## 项目负责人确认门槛

执行前，项目负责人须明确确认本文件中的：验收候选、隔离环境与回环访问边界、配置/证书来源、测试数据和账号边界、验收范围、回退与清理方案。未确认前只能进行只读预检和方案完善，不得启动 Compose、生成证书、创建测试账号/数据集，或申请任何外部资源。

## 环境边界

- 使用独立 Docker Compose 项目名：`equipment-stage7-acceptance-<随机后缀>`。
- 从验收候选构建前端和 API；记录实际 Git SHA、镜像 ID/摘要和启动时间。
- 使用 Git 忽略的 `codebase/infra/.env.local`，不得提交、打印或写入报告中的密码、Token、连接串或证书私钥。
- Nginx 只允许回环绑定 HTTPS；验证地址使用 `https://127.0.0.1:<随机本地端口>`。自签名证书只用于本机测试，浏览器信任提示不得被描述为生产安全保证。
- PostgreSQL、Redis、MinIO、ClamAV、RAGFlow 数据集、测试用户和上传附件均须为本次隔离环境专用。RAGFlow 的临时数据集在验收结束后确认删除。

## 启动前检查

1. 在具备 Docker Linux engine、Docker Compose、PowerShell、Python 3.13 与 Node 的设备上创建新的隔离工作区，并确认工作区的 `codebase/` 与验收候选一致。
2. 复制安全模板为 Git 忽略的 `codebase/infra/.env.local`，仅填入本次隔离 PostgreSQL、MinIO、RAGFlow 与 HTTPS 变量；确认所有 `change-me` 值已替换，且没有生产地址或凭据。
3. 准备仅用于本机 HTTPS 的证书目录，并选择未被占用的回环端口。不得修改默认 Compose 文件来开放 `0.0.0.0`。
4. 在启动前记录项目名、实际候选 SHA、配置文件路径而非内容、端口、RAGFlow 测试数据集标识和清理负责人。

## 启动与验收入口

1. 构建前端生产产物，并使用验证 profile 启动现有平台 Compose 服务。
2. 运行 `codebase/infra/scripts/verify-platform-readiness.ps1` 的等价受控流程，至少确认回环 HTTPS `/healthz`、静态 JS/CSS MIME、RAGFlow 探针、迁移、真实 Agent 成功/不可用降级、API 重启以及备份/隔离恢复。
3. 创建最小测试账号与非敏感测试数据后，由项目负责人通过 HTTPS 地址执行 `ACCEPTANCE_CRITERIA.md` 中适用的逐项验收。
4. 每项结果在 `ACCEPTANCE_EVIDENCE.md` 记录：AC 标识、操作者、UTC 时间、环境标识、候选 SHA、操作、结果、证据位置和缺陷编号（如有）。

## 失败、回退与清理

- 任一实现缺陷：记录缺陷，停止受影响验收项并回流 Stage 5 修复；修复后重新执行受影响的 Stage 6 和 Stage 7 证据。
- 环境故障：保留脱敏日志、容器状态和配置路径用于诊断；不得擅自删除卷或执行 `down -v`。
- 验收结束：在项目负责人确认后，仅对本次 `equipment-stage7-acceptance-*` 项目执行常规停止与受控清理；删除临时 RAGFlow 数据集、测试用户和测试附件前先记录清理结果。生产资源与无关 Docker 项目不得触碰。
