# 部署检查清单

- [ ] Stage 4 architecture and deployment topology approved
- [ ] Production build and configuration documented
- [ ] Database migrations and seed roles verified
- [ ] ECS 业务平台到 Windows RAGFlow `v0.26.3` 的受控私网连通性及真实检索成功/降级路径已验证
- [ ] Python 3.13/FastAPI runtime and OpenAI-compatible chat/Embedding/Rerank configuration supplied outside Git
- [ ] RAGFlow 保持在 Windows 独立 Docker Compose、账号和内部网络；ECS 不部署 RAGFlow 持久化依赖
- [ ] Missing-model health check fails explicitly; no pseudo-result fallback
- [ ] Agent thread persistence, SSE, interrupt/resume and audit redaction verified
- [ ] ECS 测试主机、Windows RAGFlow 主机和加密私网隧道均按环境负责人策略加固；秘密不进入仓库
- [ ] Backup at 00:10 and 10-day retention verified
- [ ] Tailscale Funnel temporary access reviewed
- [ ] Stage 6 test conclusion approved
- [ ] Stage 7 acceptance approved
