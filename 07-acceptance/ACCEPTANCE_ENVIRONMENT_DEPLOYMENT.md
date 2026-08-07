# 业务平台测试部署环境（ECS + Windows RAGFlow）

## 状态、目的与阶段边界

- 状态：已部署的业务平台测试环境；不是生产环境，也不表示 Stage 6 已通过、Stage 7 已验收或 Stage 8 已发布。
- 代码绑定：`780748cbc6b988feda66f2ebd02a6829bdafd1c1`。
- 目的：供项目负责人和同事实际查看并确认页面与业务流程，发现的问题回流当前 `TASK-013` 整改工作。
- 当前门禁：`DEF-STAGE7-001` 与 Stage 6 阻断仍未关闭；不得因页面可访问、登录成功或单项服务健康而签发验收/发布结论。

## 已批准测试部署拓扑

- 阿里云 ECS：只部署业务平台服务，使用 Compose 项目 `equipment-preview-77fbc42`；运行 PostgreSQL、Redis、MinIO、ClamAV、API、Worker、Validator、Nginx 与 Web。
- ECS 运行目录：`/opt/equipment-platform/previews/780748cbc6b988feda66f2ebd02a6829bdafd1c1`。
- RAGFlow：固定部署在本地 Windows Docker Desktop/WSL2，目标版本 `v0.26.3`；不得迁入 ECS，也不得把 RAGFlow 数据库、对象存储、卷或运行配置提交到本仓库。
- 连通性：ECS 仅经项目负责人管理的加密私网隧道调用 Windows RAGFlow API。隧道地址、认证、RAGFlow API Key、Windows 防火墙规则和私有证书均是环境秘密，不得写入 Git、PR 或测试报告。
- 测试入口：`https://101.37.16.206/`。HTTP 80 仅跳转至 HTTPS 443。当前 HTTPS 使用短期、带 IP SAN 的自签名测试证书；浏览器证书告警仅能作为测试环境告警处理，不能视作正式 PKI 方案。

## 已验证与未验证边界

本轮部署验证（2026-08-07）：systemd timer active；当前 release 和 `deployed-sha` 均绑定上述 Commit；API/Web、PostgreSQL、Redis、MinIO、ClamAV 容器运行，其中 PostgreSQL/Redis/MinIO/ClamAV healthy；公网 HTTPS `/healthz` 和根页面 HTTP 200，HTTP 入口跳转 HTTPS，JS/CSS MIME 正确。

已验证：ECS API 镜像构建、Compose 启动、数据库迁移、PostgreSQL、Redis、MinIO、ClamAV、API、Worker、Validator、Nginx、HTTPS `/healthz`、静态资源访问及 HTTP→HTTPS 跳转。

未验证：ECS 当前没有配置运行时 `RAGFLOW_API_KEY`；因此真实 RAGFlow 成功检索、引用链路与完整 Agent 成功路径尚未通过本环境验证。不得以不可用降级、HTTP 健康或 mock 结果替代该证据。

## 操作与安全要求

1. 仅使用非敏感测试数据和由环境负责人安全分发的测试账号。不得在文档、截图、日志、提交、Issue 或 PR 中记录明文账号密码、Token、Cookie、连接串、私钥、证书私钥或 `.env` 内容。
2. 若为测试新增账号、数据集或附件，应记录其用途与清理责任；不得触碰无关 ECS 数据、Docker 卷或项目。
3. 发生环境故障时，保留脱敏日志、容器状态、镜像/提交标识和配置文件路径用于排查；不得擅自执行 `down -v`、删除卷或删除 Windows RAGFlow 持久化资源。
4. 进入正式验收、交接或更广泛分发前，环境负责人必须轮换测试管理员凭据，并重新核验 RAGFlow 成功/不可用路径与受影响的 Stage 6 证据。

## 页面确认与后续验收

1. 项目负责人在测试入口按批准原型、页面功能矩阵和 `ACCEPTANCE_CRITERIA.md` 查看页面、关键状态和角色权限边界。
2. UI/交互/功能偏离登记到现有缺陷或变更台账，并在 `TASK-013` 的同一 Draft PR 中整改；不得用此环境的静态演示或临时数据直接关闭缺陷。
3. TASK-013 完成并经 DEV-001 整体审核、集成后，仍须以新的精确 Commit SHA 重做 Stage 6 独立验证；只有项目负责人另行批准，才可重新进入 Stage 7 验收。
