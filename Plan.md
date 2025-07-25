下面给出一套 **“在 OpenAI Codex 里一步步生成代码 → 推送到 GitHub → 本地或云端跑通 MVP”** 的实操攻略。整体思路是 **先固化接口规范，再用 Codex 逐服务生成骨架，最后用测试与 CI 驱动迭代**。你可以按阶段逐条复制下面的 *Prompt 模板* 到 Codex（IDE 插件或 Playground），它会自动补全代码与文档。

---

## 0 ⃣ 准备工作

| 事项       | 建议                                                                                      |
| -------- | --------------------------------------------------------------------------------------- |
| **工作区**  | 新建 GitHub 私有仓库 `agent‑research‑pay`，主干分支 `main`，保护分支规则                                  |
| **环境**   | VS Code + OpenAI Codex 插件（或 Web Playground）<br>Python 3.11, Node 18, Docker, k3d / kind |
| **目录约定** |                                                                                         |

```
.
├─ services/
│  ├─ agent-orchestrator/      # Python / FastAPI
│  ├─ payment-manager/         # Python / FastAPI
│  ├─ marketplace-api/         # Node / NestJS
│  ├─ token-issuer-mock/       # Python / FastAPI (银联沙箱)
│  └─ voiceid-service/         # Python / FastAPI
├─ infra/                      # K8s Helm charts & Terraform
├─ proto/                      # OpenAPI & gRPC specs
└─ docs/
```

---

## 1 ⃣ 先让 Codex 帮你写 **接口规范**（OpenAPI/Swagger）

> **Prompt 1：**
>
> ```text
> You are an expert API architect. Generate an OpenAPI 3.1 yaml spec for the "Marketplace API" service that has:
> - GET /company/basic?keyword=  (free)
> - GET /company/detail?id=      (returns 402 if no token)
> - POST /pay {tokenId, amount}
> Responses should follow JSON:API. Provide full schema components.
> ```

生成后保存为 `proto/marketplace.yaml`，其余服务（Agent Gateway、Payment Manager、Token Issuer）按同样套路各写一个 spec。这样后续 **Codex 会据此补全服务器实现与客户端 SDK**，并确保接口对齐。

---

## 2 ⃣ 使用 Codex 逐服务生成 **最小可运行骨架**

以下模板可直接贴在 VS Code 中的空文件里，Codex 会实时补全。

### 2.1 Agent‑Orchestrator（Python/FastAPI）

```python
"""
agent-orchestrator/main.py
Bootstraps FastAPI app handling:
- POST /tasks
- BackgroundTask to run research workflow
External deps: Payment Manager, Marketplace API, LLM core
"""
from fastapi import FastAPI, BackgroundTasks
app = FastAPI(title="Agent Orchestrator")

# === Codex will continue here ===
```

让 Codex 自动补全路由、pydantic 模型、调用逻辑，并为 `BackgroundTasks` 写 TODO 注释。

### 2.2 Payment‑Manager

```python
"""
payment-manager/main.py
Acts as façade for Token Issuer + Vault cache.
Expose:
- POST /token {budget:int, voice_id:str}
- GET /balance/{token_id}
"""
```

Codex 会补全向 Token‑Issuer mock 的 `httpx` 调用、签名校验占位函数等。

### 2.3 Marketplace‑API（Node/NestJS）

```ts
// src/app.module.ts
// Scaffold NestJS with three controllers: CatalogController, PremiumController, PaymentController
```

Codex 会生成 `@Get`, `@Post` 路由与 402 抛错逻辑。

### 2.4 Token‑Issuer‑Mock

同理，让 Codex 生成一个存内存额度表的简易沙箱。

---

## 3 ⃣ 写 **单元测试 & 集成测试** 驱动功能落地

> **Prompt 2：**
>
> ```text
> Write pytest tests that spin up Agent-Orchestrator (TestClient), Marketplace-API mock, Payment-Manager mock.
> - Scenario: user creates a task with budget 50
> - Agent requests detail -> gets 402
> - Agent pays via Payment Manager -> Marketplace returns data
> Assert: report markdown contains "company_detail"
> ```

Codex 会自动写出 `conftest.py`、`asyncio` fixtures 以及多服务 stub。

---

## 4 ⃣ Dockerfile & Compose / Helm

> **Prompt 3：**
>
> ```text
> Generate docker-compose.yaml that spins up:
> - postgres (memory store)
> - redis (short term memory)
> - agent-orchestrator : build ./services/agent-orchestrator
> - payment-manager    : …
> - marketplace-api    : …
> - token-issuer-mock  : …
> Expose orchestrator on 8000.
> ```

一键 `docker compose up` 即可本地跑完整链。后续再让 Codex 输出 `helm/` chart 供 k8s。

---

## 5 ⃣ 引入 **LLM Core** 与 RAG

1. 在 `services/agent-orchestrator/llm_core.py` 写占位类 `LLMCore`.
2. **Prompt 4：**

   ```text
   Complete LLMCore.run_research(theme:str, marketplace_client) that:
   - searches keyword via marketplace basic
   - if detail_needed -> get detail (handle 402)
   - collate result into markdown
   ```

   Codex 会补全伪检索与 Markdown 转换逻辑，稍后可替换为真正的 OpenAI o3 调用 + 向量检索。

---

## 6 ⃣ CI/CD + 代码质量

> **Prompt 5：**
>
> ```text
> Create a GitHub Actions workflow ".github/workflows/ci.yml" that:
> - sets up Python 3.11 & Node 18
> - caches pip & npm
> - runs "pytest" + "npm test"
> - on success, builds docker images with tags ${{ github.sha }} and pushes to ghcr.io
> ```

Codex 会生成工作流，记得在仓库设置 `GHCR` 密钥。

---

## 7 ⃣ 安全硬化与 TODO 列表

Codex 生成代码时，你可以在文件顶部加一段注释：

```text
# TODO (security):
# - replace in‑memory token store with Hashicorp Vault
# - add JWT auth middleware
# - enforce mTLS between internal services
```

它会在相应位置插入占位实现。

---

## 8 ⃣ 提示词小技巧

| 目的          | 提示词片段                                                                              |
| ----------- | ---------------------------------------------------------------------------------- |
| 让 Codex 写注释 | “Add detailed docstrings explaining each function’s parameters and returns.”       |
| 要求 TDD      | “Before writing implementation, write failing pytest tests first.”                 |
| 控制风格        | “Follow Google Python style guide; use type hints.”                                |
| 增量修改        | “Refactor the pay endpoint to support partial refunds; keep existing tests green.” |

---

### 小结

1. **接口先行 → 规范自动生成代码**：把 OpenAPI 描述写好，Codex 会帮你同时产出服务器端和客户端。
2. **测试驱动**：让 Codex 写测试，再补实现，确保每一步都可运行。
3. **微服务分层**：按你之前的 4 大域拆仓目录，Codex 会在局部上下文里专注生成对应服务的逻辑。
4. **CI/CD 自动化**：用 Actions 及 Docker Compose / Helm，随时 push 即可一键发布到任何云环境。

只要保持 **小 prompt → 生成 → 运行 → 反馈** 的快速循环，你可以在一两周内让 MVP 跑通，并随时替换 mock 成真实的银联、企查查生产接口。祝编码顺利!
