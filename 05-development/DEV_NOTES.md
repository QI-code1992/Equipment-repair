# 开发记录

- 状态：Stage 5 已建立工程基线
- 候选源码：`03-ui-prototype/prototype/`（仅用于设计）
- 生产源码目录：`codebase/backend/`、`codebase/frontend/`；基础设施位于 `codebase/infra/`
- 启动条件：Stage 4 架构和实施计划获批
- 规则：实现变更通过 `workflow/CHANGE_REQUESTS.md` 返回最早受影响的基线。

## 2026-07-15 · Task 1

- 建立固定生产目录：`backend/`、`frontend/`、`infra/`。
- `GET /healthz` 依据应用名、`POSTGRES_DSN`、`REDIS_URL` 进行配置级健康判断；任一缺失返回 503，全部存在返回 200。
- Compose 服务使用内部网络，未向宿主机发布 PostgreSQL、Redis 或 API 端口。
- Docker Hub 拉取 PostgreSQL/Redis 时出现 TLS EOF；Compose 通过 `DOCKER_IMAGE_PREFIX` 支持可配置镜像前缀，开发样例指向已验证可访问的镜像镜像源。该配置不改变服务名、网络或环境变量契约。

## 2026-07-15 · CR-032 代码库目录迁移

- 将正式工程目录统一迁移为 `codebase/backend/`、`codebase/frontend/`、`codebase/infra/`。
- `03-ui-prototype/prototype/` 保持原位，继续作为 Stage 3 原型唯一事实来源；未创建 `codebase/prototype/`。
- 未保留旧目录兼容副本；后续开发、测试和部署命令必须使用 `codebase/` 路径。
