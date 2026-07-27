# TASK-010 最小登录与会话入口设计

## 目标

关闭 PR #50 的认证 P1：让正式前端能够调用既有 `/api/auth/login`，将成功会话 token 写入浏览器会话存储，并让受保护页面及 JSON/SSE API 调用使用该 token。

## 范围与边界

- 新增正式 `/login` 页面、登录 API 客户端、会话 token 读写和未认证路由保护。
- 登录成功后回到原始受保护路径；直接访问 `/login` 的已认证用户进入工作台。
- 复用 `sessionStorage.access_token`；token 不进入 React 状态、日志、页面文本或 URL。
- 不修改后端认证规则、公开 API、数据库、部署、依赖、Stage 3 原型或现有业务页面契约。

## 方案

认证状态只由 `sessionStorage.access_token` 是否为非空字符串决定。`LoginPage` 调用 `login(username, password)`；成功后写 token 并通过 React Router 跳转。`RequireAuthentication` 使用 `Navigate` 将无 token 用户送至 `/login`，并以 `location.pathname` 保存返回目标。

`api.ts` 保持单一网络边界：JSON 请求和 Runtime SSE 均在 fetch 前从同一会话存储读取 token 并加入 Bearer 头。登录请求自身不附加该头。

## 失败与测试

- 登录失败显示统一的账号或密码错误提示，不显示服务端细节或 token。
- 认证态为无 token 时不能渲染受保护页面；登录后才允许访问并由 API 边界发送 Bearer。
- 回归覆盖未认证重定向、登录成功写入和跳回、失败提示、登录后的 JSON/SSE 认证头。
