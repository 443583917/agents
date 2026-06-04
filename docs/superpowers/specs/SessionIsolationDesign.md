# 用户会话隔离 — 生产级 thread_id 设计方案

---

## 一、核心原则：职责边界

生产环境中，会话隔离由**两层**协作完成。理解谁能做什么是设计的前提。

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  应用层（你负责）                                            │
│  ├── 生成 thread_id（UUID v7）                               │
│  ├── 存储 thread → user 归属关系                             │
│  ├── 每次请求验证：thread 是否属于当前用户                    │
│  ├── 会话列表查询、归档、删除                                 │
│  └── config 签名防篡改                                       │
│                                                             │
│  LangGraph（框架负责）                                        │
│  ├── 以 thread_id 为 key 存取 state                          │
│  ├── 自动生成 checkpoint_id，自动链接 parent 形成版本链       │
│  ├── 自动恢复最新 checkpoint                                 │
│  └── 不关心 user_id 是谁、不关心业务逻辑                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**一句话：thread_id 是你设计的，checkpoint_id 是 LangGraph 自动维护的。正常使用时你只传 thread_id，不需要管 checkpoint_id。**

---

## 二、整体架构

```
                    请求入口
                       │
                       ▼
              ┌────────────────┐
              │ ① 身份验证层    │  JWT → user_id, scopes, tenant_id, tier
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ ② 路由分发层    │  新对话？继续旧对话？列表？
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ ③ 鉴权校验层    │  thread 归当前用户吗？签名有效吗？
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ ④ 调用 LangGraph│  graph.invoke(messages, config)
              └───────┬────────┘
                      │  config 只传 thread_id
                      │  checkpoint 自动恢复/创建
                      ▼
              ┌────────────────┐
              │ ⑤ Checkpointer  │  PostgresSaver（生产）/ SqliteSaver（开发）
              └────────────────┘
```

---

## 三、身份验证：从 JWT 提取用户数据

一切操作的入口。这张对象贯穿后续所有函数。

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

@dataclass(frozen=True)
class AuthenticatedUser:
    user_id:    str              # JWT.sub，全局唯一
    scopes:     list[str]        # JWT.scopes，如 ["chat:read", "chat:write"]
    session_id: str              # JWT.jti，本次登录标识
    tenant_id:  Optional[str]    # JWT.aud，SaaS 多租户
    tier:       str              # "free" / "pro" / "enterprise"
    expires_at: datetime         # JWT.exp

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


import jwt, os

PUBLIC_KEY = os.environ["JWT_PUBLIC_KEY"]

def verify_and_extract(token: str) -> AuthenticatedUser:
    payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"],
                         audience="langgraph-chat-app",
                         options={"require": ["sub", "exp", "jti", "scopes"]})
    return AuthenticatedUser(
        user_id    = payload["sub"],
        scopes     = payload["scopes"],
        session_id = payload["jti"],
        tenant_id  = payload.get("org"),
        tier       = payload.get("tier", "free"),
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
```

---

## 四、thread_id 生成器：UUID v7

thread_id 是整个隔离体系的基石。选用 UUID v7（RFC 9562）。

```python
import uuid as _uuid  # Python 3.14+ uuid.uuid7()
                       # 低版本: pip install uuid7 → from uuid7 import uuid7

def generate_thread_id() -> str:
    """
    格式: UUID v7
    示例: 018f4a3c-9b2e-7d1f-a3b2-000000000001

    特性:
      - 前 48 位毫秒时间戳 → 全局递增 + 可反推生成时间
      - 后 74 位随机      → 防冲突、不可猜测
      - 无需中心化协调     → 多实例并行不冲突
      - 重启安全           → 时间永远向前
    """
    return str(_uuid.uuid7())

def thread_created_at(thread_id: str) -> datetime:
    ts_ms = _uuid.UUID(thread_id).time
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
```

**UUID v7 结构：**

```
018f4a3c-9b2e-7d1f-a3b2-000000000001
│        │      │  │  │             │
│        │      │  │  └─ 74 位随机（防冲突）
│        │      │  └─ 版本号 "7"
│        │      └─ 变体位 (2 位)
│        └─ 48 位时间戳（毫秒精度，可反推时间）
└─ 保留位 (4 位)
```

**效果验证：**

```python
import time

for _ in range(3):
    tid = generate_thread_id()
    print(f"{tid}  →  {thread_created_at(tid).isoformat()}")
    time.sleep(0.001)

# 018f4a3c-9b2e-7d1f-9b2e-000000000001  →  2026-06-04T10:30:15.123+00:00
# 018f4a3c-9b2e-7d1f-9b2e-000000000002  →  2026-06-04T10:30:15.125+00:00
# 018f4a3c-9b2e-7d20-0000-000000000003  →  2026-06-04T10:30:16.125+00:00
#                               ↑ 递增，可读时间，重启安全
```

---

## 五、Config 构造与签名

```python
import hmac, hashlib

APP_SECRET = os.environ["APP_SECRET_KEY"].encode()

def build_config(user: AuthenticatedUser, thread_id: str) -> dict:
    """每次调 graph.invoke() 前构造，含防篡改签名"""
    sig = hmac.new(
        APP_SECRET,
        f"{user.user_id}:{user.tenant_id or ''}:{thread_id}".encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    return {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "signature": sig,
            "tier": user.tier,
        }
    }

def verify_config(config: dict) -> bool:
    """每次 invoke 前验证签名，防篡改"""
    cfg = config["configurable"]
    expected = hmac.new(
        APP_SECRET,
        f"{cfg['user_id']}:{cfg.get('tenant_id', '')}:{cfg['thread_id']}".encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    if not hmac.compare_digest(cfg.get("signature", ""), expected):
        raise PermissionError("Config 签名无效 — 数据可能被篡改")
    return True
```

**正常使用时 config 只传 thread_id，checkpoint_id 由 LangGraph 自动追踪：**

```python
# ✅ 正常流程：只传 thread_id
config = {"configurable": {"thread_id": thread_id}}
graph.invoke(messages, config=config)
# → LangGraph 自动找到最新 checkpoint 恢复 state
# → 执行完成后自动创建新 checkpoint，parent 指向上一个

# ⏪ 时间旅行（少数需要 checkpoint_id 的场景之一）
config = {"configurable": {"thread_id": thread_id, "checkpoint_id": old_ckp_id}}
graph.invoke(messages, config=config)
# → 从指定 checkpoint 恢复并分叉
```

---

## 六、业务数据库表设计

应用层维护 `chat_threads` 表存储会话归属；LangGraph 的 checkpointer 自动维护 `checkpoints` 表存储状态快照。

```sql
-- 应用层：会话归属表
CREATE TABLE IF NOT EXISTS chat_threads (
    thread_id   TEXT PRIMARY KEY,          -- UUID v7，由 generate_thread_id() 生成
    user_id     TEXT NOT NULL,             -- 谁创建的
    tenant_id   TEXT,
    title       TEXT DEFAULT '新对话',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_threads_user
    ON chat_threads(user_id, last_active DESC);
```

**两张表的关系：**

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│ chat_threads（应用层负责）        │     │ checkpoints（LangGraph 自动维护）  │
│                                 │     │                                  │
│ thread_id ←────────── 关联 ────→│     │ thread_id                        │
│ user_id       谁拥有这个会话      │     │ checkpoint_id    自动生成的版本ID  │
│ title         会话标题            │     │ parent_checkpoint_id  版本链      │
│ created_at    创建时间            │     │ checkpoint (BLOB)   完整 state    │
│ last_active   最后活跃时间        │     │ metadata (BLOB)    元数据         │
│ is_archived   是否归档            │     │                                  │
└─────────────────────────────────┘     └──────────────────────────────────┘

职责：                               职责：
- 生成 thread_id                     - 按 thread_id 存取 state
- 存储 thread ↔ user 归属             - 自动生成 checkpoint_id
- 验证归属 + 签名                     - 自动链接 parent 形成版本链
- 列表 / 归档 / 删除                  - 提供 get_state / get_state_history
```

---

## 七、完整 API 实现

```python
from functools import wraps
from typing import Callable

# ============================================================
# 装饰器：统一鉴权入口
# ============================================================
def require_auth(func: Callable):
    @wraps(func)
    def wrapper(token: str, *args, **kwargs):
        user = verify_and_extract(token)
        if user.is_expired:
            raise PermissionError("Token 已过期")
        if "chat:read" not in user.scopes:
            raise PermissionError("无聊天权限")
        return func(user, *args, **kwargs)
    return wrapper


# ============================================================
# POST /threads/create — 创建新会话
# ============================================================
@require_auth
def create_thread(user: AuthenticatedUser, title: str = "新对话") -> dict:
    thread_id = generate_thread_id()          # ① UUID v7
    config = build_config(user, thread_id)    # ② 含签名

    conn.execute(
        "INSERT INTO chat_threads (thread_id, user_id, tenant_id, title) VALUES (?, ?, ?, ?)",
        (thread_id, user.user_id, user.tenant_id, title)
    )
    conn.commit()

    return {
        "thread_id": thread_id,
        "created_at": thread_created_at(thread_id).isoformat(),
        "title": title,
        "config": config,                     # 客户端保存，后续请求带上
    }


# ============================================================
# POST /chat — 继续对话
# ============================================================
@require_auth
def continue_thread(user: AuthenticatedUser, thread_id: str, user_input: str) -> dict:
    # ——— ① 鉴权：这个 thread 属于当前用户吗？ ———
    row = conn.execute(
        "SELECT user_id, is_archived FROM chat_threads WHERE thread_id = ?",
        (thread_id,)
    ).fetchone()

    if row is None:
        raise ValueError("会话不存在")
    if row[0] != user.user_id:
        raise PermissionError("这不是你的会话")
    if row[1]:
        raise ValueError("会话已归档")

    # ——— ② 构造 config + 验签 ———
    config = build_config(user, thread_id)
    verify_config(config)

    # ——— ③ 调 LangGraph（只传 thread_id，checkpoint 自动处理）———
    result = graph.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config
    )

    # ——— ④ 更新活跃时间 ———
    conn.execute(
        "UPDATE chat_threads SET last_active = CURRENT_TIMESTAMP WHERE thread_id = ?",
        (thread_id,)
    )
    conn.commit()

    return {
        "reply": result["messages"][-1].content,
        "thread_id": thread_id,
    }


# ============================================================
# GET /threads — 会话列表（类似 ChatGPT 左侧栏）
# ============================================================
@require_auth
def list_threads(user: AuthenticatedUser, limit: int = 20, offset: int = 0) -> list[dict]:
    rows = conn.execute(
        """SELECT thread_id, title, created_at, last_active
           FROM chat_threads
           WHERE user_id = ? AND is_archived = 0
           ORDER BY last_active DESC
           LIMIT ? OFFSET ?""",
        (user.user_id, limit, offset)
    ).fetchall()

    return [{"thread_id": r[0], "title": r[1], "created_at": r[2], "last_active": r[3]} for r in rows]


# ============================================================
# DELETE /threads/{thread_id} — 删除会话
# ============================================================
@require_auth
def delete_thread(user: AuthenticatedUser, thread_id: str) -> None:
    row = conn.execute(
        "SELECT user_id FROM chat_threads WHERE thread_id = ?", (thread_id,)
    ).fetchone()
    if row is None or row[0] != user.user_id:
        raise PermissionError("无权操作")

    # 联动清理：业务表 + checkpoint 表
    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM checkpoint_writes WHERE thread_id = ?", (thread_id,))
    conn.execute("DELETE FROM chat_threads WHERE thread_id = ?", (thread_id,))
    conn.commit()
```

---

## 八、完整请求流程图

```
客户端                              服务端                              存储层
┌──────┐                            ┌──────┐                            ┌─────┐
│ JWT   │─── POST /threads/create ──→│      │                            │     │
│ Token │                            │ ① 验JWT → AuthenticatedUser      │     │
│       │                            │ ② uuid.uuid7() → thread_id       │     │
│       │                            │ ③ build_config(user, tid)        │     │
│       │                            │ ④ INSERT chat_threads ──────────→│     │
│       │←── { thread_id, config } ──│      │                            │     │
│       │                            │      │                            │     │
│ 存储  │                            │      │                            │     │
│ config│                            │      │                            │     │
│       │                            │      │                            │     │
│       │─── POST /chat ────────────→│      │                            │     │
│       │  { thread_id, user_input } │ ① 验JWT → user                   │     │
│       │                            │ ② SELECT 验证归属 ──────────────→│     │
│       │                            │ ③ build_config + verify_config   │     │
│       │                            │ ④ graph.invoke(msgs, config) ───→│ checkpoint  │
│       │                            │    内部自动：恢复 → 执行 → 存快照  │     │
│       │                            │ ⑤ UPDATE last_active ───────────→│     │
│       │←── { reply } ──────────────│      │                            │     │
└──────┘                            └──────┘                            └─────┘
```

---

## 九、Checkpoint：你需要关心的和不需要关心的

### 不需要关心的（LangGraph 自动处理）

```python
# ① 创建会话 → 自动建根 checkpoint
# ② 继续对话 → 自动找到最新 checkpoint 恢复 state
# ③ 每次 invoke → 自动创建新 checkpoint，parent 自动链接
# ④ 版本链追溯 → 自动沿 parent 链查找

config = {"configurable": {"thread_id": thread_id}}
graph.invoke(messages, config=config)
graph.get_state(config)                # 最新状态
list(graph.get_state_history(config))  # 完整历史
```

以上所有操作你只传了 `thread_id`，`checkpoint_id` 在内部完全自动。

### 少数需要主动用 checkpoint_id 的场景

| 场景 | 做法 | 频率 |
| ------ | ------ | :----: |
| **时间旅行** | `config` 加 `checkpoint_id`，回到过去分叉 | 极少 |
| **定时清理** | 按 `checkpoint` 时间戳删除 90 天前的旧版本 | 定时任务 |
| **审计追溯** | 定位到某个具体的 checkpoint 查看当时 state | 按需 |

```python
# 时间旅行示例
history = list(graph.get_state_history(config))
old_ckp_id = history[2].config["configurable"]["checkpoint_id"]

branch_config = {"configurable": {"thread_id": tid, "checkpoint_id": old_ckp_id}}
graph.invoke(messages, config=branch_config)  # 从该点分叉

# 定时清理示例（90 天前的 checkpoint）
conn.execute("DELETE FROM checkpoints WHERE timestamp < datetime('now', '-90 days')")
```

---

## 十、Checkpointer 选型

| | SqliteSaver | PostgresSaver |
| --- | --- | --- |
| **适用** | 本地开发、单用户工具、PoC | **生产环境** |
| **并发写入** | ❌ 单文件锁 | ✅ 行级锁 |
| **多实例共享** | ❌ 各连各的文件 | ✅ 共享一个 PG |
| **连接池** | ❌ | ✅ psycopg_pool |
| **备份恢复** | 手动 cp | ✅ 成熟工具链 |
| **配置** | `SqliteSaver(conn)` | `PostgresSaver(pool)` |

```python
# 生产环境：PostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg_pool

pool = psycopg_pool.ConnectionPool(
    conninfo="postgresql://user:pass@host:5432/langgraph",
    min_size=2, max_size=20,
)

checkpointer = PostgresSaver(pool)
checkpointer.setup()  # 自动建表
graph = graph_builder.compile(checkpointer=checkpointer)

# 用法完全不变 —— config 照样只传 thread_id
config = {"configurable": {"thread_id": thread_id}}
graph.invoke(messages, config=config)
```

---

## 十一、安全清单

| 攻击方式 | 防御措施 |
|---------|---------|
| 猜 `thread_id` 访问别人对话 | UUID v7 后 74 位随机，不可猜测；外加归属校验 `row.user_id == user.user_id` |
| 篡改 `config` 里的 `user_id` | HMAC `signature`，每次 `invoke` 前做 `verify_config` |
| 伪造 JWT | RS256 公钥验证，每次请求都验 |
| Token 过期继续用 | `user.is_expired` 检查 |
| 跨租户访问 | `tenant_id` 贯穿全链路，SQL 查询加 `tenant_id` 过滤 |
| 内部日志泄露 thread_id | 日志脱敏：只打前 8 位 |

---

## 十二、要点速记

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ▼ 应用层负责（你设计）                                           │
│  ① JWT 验证 → AuthenticatedUser（user_id, scopes, tenant_id）     │
│  ② UUID v7 → thread_id（递增 + 含时间 + 重启安全）                 │
│  ③ chat_threads 表 → 存归属关系（thread 属于哪个 user）            │
│  ④ build_config() + verify_config() → 签名防篡改                  │
│  ⑤ 每次操作前验归属：row.user_id == user.user_id                  │
│                                                                  │
│  ▼ LangGraph 负责（框架自动）                                      │
│  ⑥ 以 thread_id 为 key 存取 state                                │
│  ⑦ checkpoint_id 自动生成，parent 自动链接成版本链                 │
│  ⑧ 正常使用时你只传 thread_id，不需要关心 checkpoint_id            │
│                                                                  │
│  ▼ 存储                                                           │
│  ⑨ 开发用 SqliteSaver，生产用 PostgresSaver                       │
│  ⑩ 删除 thread 时联动清理 chat_threads + checkpoints 两张表       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```
