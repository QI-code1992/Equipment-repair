# TASK-011 附件安全与 Nginx HTTPS 设计

## 状态与边界

- 变更：CR-044，已获项目负责人范围确认，待本设计书面复核后实施。
- 当前阶段：Stage 5；本设计不构成 Stage 6、Stage 7 或生产发布批准。
- 目标：在不改变故障上报 `attachment_refs` 契约的条件下，新增受控附件上传/扫描能力，并用 Nginx 提供唯一 HTTPS 入口。
- 排除：不新增数据库迁移、外部依赖、对象下载/预览、断点续传、病毒库运维、工厂或设备行级授权、公开 HTTP 回退。

## 附件上传与扫描

### API

`POST /api/attachments`：要求已有 `fault:create` 权限、Bearer 会话和非空 `Idempotency-Key`；请求为 `multipart/form-data`，只含一个 `file` 字段。成功响应为既有 `AttachmentRef`：`object_key,filename,size_bytes,content_type`。幂等摘要包含文件 SHA-256、文件名、MIME 与大小；同 Key 重放原响应，不同摘要返回既有 409。审计或提交失败时回滚数据库并删除刚写入对象。

调用方只能把成功返回的引用放进既有 `POST /api/fault-reports` 或 Agent 故障上报草稿的 `attachment_refs`。这两个 API 的请求、响应、幂等和业务状态机不改变。

### 处理顺序

1. 拒绝缺失文件、空文件、超过 100 MiB 的文件，以及不在以下允许 MIME 集合内的文件：`image/jpeg`、`image/png`、`image/webp`、`application/pdf`、`text/plain`、`text/csv`、`application/msword`、`application/vnd.openxmlformats-officedocument.wordprocessingml.document`、`application/vnd.ms-excel`、`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。`.zip` 等压缩包、宏格式和其他类型均拒绝。
2. 将请求流写入受控临时文件，文件名由服务端随机化；不信任客户端路径或对象键。
3. 使用现有 ClamAV 集成扫描临时文件；感染、扫描超时或扫描服务不可用均返回稳定错误，不写 MinIO。
4. 扫描成功后通过既有 MinIO 集成写入按随机 UUID 生成的对象键；响应只返回元数据。
5. 无论成功或失败均清理临时文件；对象写入失败不返回可引用对象。审计只记录动作、结果、文件名、类型、大小和对象键，禁止正文、字节、Base64、密码、Token、Cookie 与连接串。

### 错误与测试

- `422 ATTACHMENT_INVALID`：缺失、空文件、大小或 MIME 不合规。
- `422 ATTACHMENT_INFECTED`：ClamAV 明确判定感染。
- `503 ATTACHMENT_SCAN_UNAVAILABLE`：扫描超时或扫描服务不可用。
- `503 ATTACHMENT_STORAGE_UNAVAILABLE`：对象存储写入失败。

TDD 覆盖未认证/无权限、100 MiB 边界、允许/拒绝 MIME、感染、扫描不可用、存储失败、临时文件清理、成功返回的引用可提交到既有故障 API，以及审计脱敏。

## Nginx HTTPS

- Compose 新增唯一 `nginx` 服务，宿主仅绑定 `127.0.0.1:${NGINX_HTTPS_PORT}:443`。
- 证书与私钥只从 Git 忽略的本地目录挂载；`.env.example` 仅提供路径和端口占位，不含证书或私钥。
- Nginx 对 `/api/` 代理 FastAPI；对 `/api/agent/runs/` 关闭缓冲、保留升级头并使用有限读取超时，以维持 SSE。
- PostgreSQL、Redis、MinIO、ClamAV、Worker、RAGFlow、Elasticsearch 均不得有宿主机端口。Nginx 无证书、上游不可用或健康检查失败时明确失败，不暴露明文 HTTP。

## 验证与回滚

- 静态验证解析 Compose，断言端口唯一性、证书挂载、API/SSE 代理与禁止明文 HTTP。
- 真实验证用仓库外 RAGFlow Key 与 Git 忽略的 `.env.local` 启动 Docker；检查 HTTPS `/healthz`、附件安全失败路径、Agent/RAGFlow 降级、端口隔离、容器重启和备份恢复。
- 回滚使用 TASK-011 的独立提交选择性 `git revert`；不删除 MinIO 中已有业务附件，不执行 `docker compose down -v`。
