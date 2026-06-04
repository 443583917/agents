# Go 多 Agent 协作集群架构设计

**日期**: 2026-06-03
**状态**: Approved
**作者**: 夏之

## 1. 概述

### 1.1 背景

作为一名 Go 开发者，拥有多个现有的业务系统项目，现在要引入 AI Agent 做系统决策。需要在多 Agent 协作场景下，充分发挥 Go 的内存模型和并发优势支撑这些"数字劳动力"，同时具备完善的服务过载降级能力。

### 1.2 需求摘要

| 维度 | 选择 |
|------|------|
| 决策域 | 基础设施 + 业务逻辑 + 运维自愈（全覆盖） |
| 协作模式 | 集中编排 + 对等协商 + 层级式（混合） |
| 延迟要求 | 毫秒级（风控/路由）+ 百毫秒级（推荐/扩缩容）+ 秒级（批量审核/周期性调优） |
| 集成形态 | 独立 Agent 集群，业务系统通过 RPC/消息队列远程调用 |

### 1.3 核心设计原则

- **Go 原生**: 每个 Agent 实例 = 一个 goroutine + 一个 channel inbox，Go runtime 即调度中心
- **分层架构**: 按延迟要求分 L0/L1/L2 三层，每层独立的通信模式和降级边界
- **渐进降级**: 五层降级信号体系，从单 Agent 隔离到全局熔断逐层升级
- **渐进落地**: 四个阶段逐步引入，每个阶段可独立上线、可回滚

## 2. 整体架构

```
                        ┌──────────────────────────┐
                        │     Agent Gateway         │
                        │  (统一入口，协议适配层)      │
                        └──────┬──────────┬────────┘
                               │          │
              ┌────────────────┼──────────┼────────────────┐
              │                │          │                │
     ┌────────▼────────┐  ┌───▼──────────▼───┐  ┌────────▼────────┐
     │  L0 Hot Engine   │  │  L1 Warm Engine  │  │  L2 Cold Engine │
     │  (进程内嵌入)     │  │  (Agent Pod集群)  │  │  (Worker Pool)  │
     │                  │  │                  │  │                 │
     │  • 纯内存决策     │  │  • gRPC 同步调用  │  │  • NATS 异步消费 │
     │  • < 10ms        │  │  • 100-500ms     │  │  • 1s-30s       │
     │  • 无外部依赖     │  │  • 有状态Agent   │  │  • 事件溯源     │
     └────────┬────────┘  └───┬──────────────┘  └────────┬────────┘
              │               │                          │
              └───────────────┼──────────────────────────┘
                              │
              ┌───────────────┼──────────────────────────┐
              │               │                          │
     ┌────────▼────────┐  ┌───▼──────────┐  ┌───────────▼─────┐
     │  Agent Registry  │  │  Degradation │  │  Decision Store  │
     │  (etcd/consul)   │  │  Controller  │  │  (EventStore)    │
     │  • Agent发现     │  │  • 全局降级   │  │  • 审计追踪      │
     │  • 健康检查      │  │  • 分层熔断   │  │  • 状态回放      │
     └─────────────────┘  └──────────────┘  └──────────────────┘
```

### 2.1 三层引擎分工

| 维度 | L0 Hot | L1 Warm | L2 Cold |
|------|--------|---------|---------|
| 典型场景 | 风控拦截、流量路由 | 推荐策略、自动扩缩容 | 批量审核、周期性调优 |
| Agent 形态 | 轻量规则 + 可选模型推理 | 有状态 Agent goroutine | 无状态 Worker goroutine |
| 通信方式 | 函数调用/共享内存 channel | gRPC unary/bidi stream | NATS JetStream queue |
| 延迟目标 | < 10ms P99 | < 500ms P99 | < 30s |
| 扩缩方式 | 随业务进程扩缩 | 独立 HPA | KEDA + NATS pending |

### 2.2 关键设计决策

1. **Agent Gateway 作为统一入口**: 业务系统不需要知道 Agent 在哪一层，Gateway 根据 `(decision_type, latency_budget, priority)` 三元组路由
2. **每层独立降级边界**: Hot 层过载不影响 Warm 层
3. **Decision Store 共享底座**: 所有层决策结果最终落入 EventStore，提供跨层审计

## 3. Agent 生命周期与 Go 并发模型

### 3.1 核心原则

**每个 Agent = 一个 goroutine + 一个 channel inbox**。Go runtime 负责调度成千上万个 Agent goroutine。

### 3.2 Agent 基础抽象

```go
type Agent interface {
    ID()      string
    Role()    AgentRole          // Orchestrator / Specialist / Executor
    Decide(ctx context.Context, input DecisionInput) (Decision, error)
    Capabilities() []Capability
}

type AgentRuntime struct {
    agent    Agent
    inbox    chan Envelope         // 有缓冲 channel = Agent 收件箱
    outbox   chan Envelope
    state    *AgentState           // 仅本 goroutine 读写，无锁
    metrics  *AgentMetrics
    cancel   context.CancelFunc
}
```

### 3.3 L0 Hot Path Agent — 零开销模型

复用调用方 goroutine，不创建独立 goroutine：

- 规则引擎优先（纳秒级）
- `modelPool` 有界 channel 做并发控制
- `select { case client := <-pool: ... case <-ctx.Done(): ... default: fallback }` 三路覆盖所有情况

### 3.4 L1 Warm Path Agent — select-loop 事件循环

每个 Agent 是独立 goroutine，持有专属收件箱和状态：

- `select { case msg := <-inbox: handle case <-ctx.Done(): shutdown }`
- Agent 状态仅本 goroutine 读写，无锁设计
- `context.WithTimeout` 提供单次决策超时保护

### 3.5 L2 Cold Path Worker Pool

Goroutine pool 消费 NATS 消息：

- 有界 `tasks chan` = 任务队列 + 反压阀
- `semaphore chan struct{}` 做并发控制信号量
- 消费者可动态扩缩（KEDA 驱动）

### 3.6 多 Agent 协作并发模式

**Fan-Out / Fan-In（集中编排）**:
- Orchestrator 拆解任务 → goroutine per subtask → WaitGroup 等待 → 聚合
- 有缓冲 result channel 防 goroutine 泄漏

**Pub/Sub 广播（对等协商）**:
- `select { case sub <- msg: default: }` 非阻塞发送，慢消费者不拖累快消费者
- 超时窗口内收集挑战/异议

### 3.7 Go 内存模型安全保证

| 场景 | Go 机制 | 保证 |
|------|---------|------|
| Agent 间消息传递 | channel send → recv | send 前的所有写对 recv 后可见 |
| Agent 启动 | `go func()` | go 语句前的写对 goroutine 内可见 |
| Agent 结束 | `sync.WaitGroup.Done()` | goroutine 内的写对 Wait() 后可见 |
| 超时取消 | `context.WithTimeout` | 取消信号通过 Done() channel 传播 |
| 共享配置热更新 | `sync/atomic` 或 `sync.RWMutex` | 读写锁保证可见性 |

## 4. 队列设计与上下文传递

### 4.1 分场景队列架构

不同协作类型需要不同的队列语义：

| 协作类型 | 队列语义 | 原因 |
|---------|---------|------|
| Orchestrator + Specialists | 有状态编排队列 | 需追踪所有子 Agent 完成状态 |
| Peer 协商 | 广播 + 超时窗口 | 不能因某个 Agent 慢就卡死 |
| Pipeline 链式 | 顺序队列 | 保证顺序和背压传导 |
| 批量独立 | 工作队列，抢占式消费 | 无所谓谁处理 |

### 4.2 编排队列实现

- `OrchestrationQueue.pending` 有缓冲 channel 作为编排请求入口
- 支持 DAG 依赖调度：子任务完成后检查依赖关系，unblock 下游任务
- 子 Agent 超时/过载时：该子任务标记失败，其余子任务不受影响

### 4.3 上下文传递原则

**传引用不传值，每个 Agent 只拿需要的切片**。

三种策略按场景选择：

| 策略 | 适用层 | 描述 |
|------|--------|------|
| 零拷贝 | L0 Hot | `ctx.Value` 存指针，同进程内直接读共享内存 |
| Reference + Lazy Fetch | L1 Warm | 传上下文引用 ID，Agent 按需从 ContextStore 拉取 |
| Embedded Subset | L2 Cold | 消息自带上下文子集，消费者无需回查 |

### 4.4 SharedContext 设计

- `SharedContext` 一次构建，按 Agent role 定义可见字段 (`SetView`)
- `ContextView` 仅包含该 role 需要的字段 + 必要的 `DecisionMetadata`
- `SharedContext.version` 提供乐观锁，合并时检测冲突
- 降级友好：ContextStore 不可用时用本地缓存兜底

## 5. 服务过载降级 — 五层状态机

### 5.1 降级信号层次

```
L1: Agent 实例健康 → 单 Agent 错误率/超时率
L2: 延迟劣化     → P99 latency / Timeout rate
L3: 队列反压     → Channel buffer usage / Queue depth
L4: 资源过载     → CPU / Mem / Goroutine count
L5: 全局过载保护  → 自适应减载 (Gradient-based)
```

### 5.2 降级状态定义

| 状态 | 含义 | L0 | L1 | L2 |
|------|------|-----|-----|-----|
| Normal | 全功能 | 正常 | 正常 | 正常 |
| Guarded | 轻度限流 | 正常 | 并发减半，摘除坏 Agent | 采样消费(每 10 条 1 条) |
| Restricted | 重度限流 | 正常 | 只处理高优先级 | 暂停消费，低优丢弃 |
| Degraded | 全局降级 | 规则模式 | 拒绝新请求 | 清理队列 |
| Emergency | 紧急熔断 | 静态规则 | 拒绝所有 | 关闭消费者，死信兜底 |

### 5.3 降级决策表（完整）

| 信号 | Guarded | Restricted | Degraded | Emergency |
|------|---------|------------|----------|-----------|
| L0 Hot | 正常 | 正常 | 规则模式 | 静态规则 |
| L1 Warm | 并发减半, 摘除坏 Agent | 只处理高优先级 | 拒绝新请求, 排空 inbox | 拒绝所有, 强制排空 |
| L2 Cold | 采样消费 (1/10) | 暂停消费, 低优丢弃 | 清理队列, 缩容 | 关闭消费者, 死信兜底 |
| Gateway | 令牌桶减速 | 只放高优 | 全部返回兜底决策 | 拒绝所有, 返回 503 |
| Pool | 缩到 50% | 停止扩容 | 缩到最小 | 全部停止 |
| 恢复条件 | 信号<阈值 持续 30s | 信号<阈值 持续 60s | 信号<阈值 持续 120s | 信号<阈值 持续 300s + 手动确认 |

### 5.4 自适应并发限制

Gradient-based concurrency limiting（参考 Netflix Adaptive Concurrency Limit）:

- 采样最近延迟，计算延迟变化梯度
- 延迟恶化 > 20% → 激进降低并发上限（×0.7）
- 延迟改善 > 10% → 缓慢恢复并发上限（×1.05）
- 以 `runtime.NumGoroutine()` 作为当前并发数

### 5.5 恢复机制

- 恢复比降级更保守，防止震荡
- 10 分钟内降级超过 3 次 → 恢复间隔翻倍
- 每层独立恢复，互不影响

## 6. 监控与告警

### 6.1 监控分层

```
L4: 业务影响层 — 决策采纳率、用户体验指标、收入影响
L3: 决策质量层 — Agent vs 规则对比、决策漂移、幻觉率
L2: Agent 运行层 — 每个 Agent 的延迟/错误率/超时率、协作链路
L1: 基础设施层 — Goroutine 数、Channel buffer、CPU/Mem/NATS
```

### 6.2 核心监控指标

| 类别 | 指标 | 描述 |
|------|------|------|
| SLI | agent_decision_success_rate | Agent 决策成功率，最核心的服务水平指标 |
| SLI | agent_fallback_rate | 降级到规则的频率，按原因拆分(timeout/error/overload/unsafe) |
| Latency | agent_decision_latency_seconds | 分层延迟分布 (Histogram, 1ms-10s buckets) |
| Quality | agent_drift_score | 决策分布与历史基线的偏差，模型退化早期预警 |
| Quality | agent_rule_agreement_rate | Agent 与规则引擎决策一致率 |
| Quality | hallucination_rate | 输出不在合理范围的比率 |
| Queue | agent_inbox_utilization | 收件箱利用率 (depth/capacity) |
| Resource | goroutines_gauge | Goroutine 数量及增长速率 |
| Resource | adaptive_limit | 自适应并发上限当前值 |
| Safety | unsafe_blocked_total | 安全护栏拦截次数 |
| Collab | orchestration_health | 编排任务在目标时间内完成的比例 |
| Degradation | degradation_state | 各层当前降级状态 |

### 6.3 告警规则

**P0 紧急（立即 On-Call）**:
- 全局降级状态达到 Emergency
- 全局决策成功率 < 90%
- Goroutine 泄漏（> 100000 或增长速率 > 1000/min）

**P1 严重（30 分钟内响应）**:
- Fallback 率 (timeout) > 10%
- 决策漂移分数 > 0.3
- 编排健康度 < 90%

**P2 警告（工作时间处理）**:
- Agent 收件箱利用率 > 70%
- Warm Path P99 延迟 > 500ms
- 安全护栏频繁拦截 (> 1%)

### 6.4 Grafana Dashboard 布局

**Dashboard 1: Agent 系统总览（运维视角）**:
- 全局状态条 + 核心 SLI 大数字
- 决策延迟分布 Heatmap（L0/L1/L2 三层）
- 降级事件时间线 + Agent 健康矩阵灯号
- 资源面板（Goroutine/CPU/Memory/Channel Buffer/NATS Pending）

**Dashboard 2: 决策质量分析（数据/算法视角）**:
- 决策质量趋势（一致率 + 漂移分数 7 天趋势）
- Agent vs 规则分歧热力图
- 决策来源分布（Agent/Rule/Cache）按决策点
- Fallback 原因分布 + 安全护栏拦截明细

**Dashboard 3: 多 Agent 协作追踪（调试视角）**:
- 编排任务瀑布图（子任务耗时 + 依赖链）
- Agent 调用拓扑图（节点颜色 = 延迟健康度, 连线粗细 = 调用量）
- 上下文传递链路（数据血缘 + 数据量节省比）

### 6.5 告警自动响应

- `AgentHighFallbackRate` → 自动降低并发度，Gateway 只放高优先级
- `GoroutineLeak` → 自动 dump goroutine profile，隔离增长最快的 Agent
- `DecisionDriftDetected` → 该 Agent 降级为 Shadow 模式，通知数据科学团队
- `UnsafeDecisionBlocked` (>5%) → 该决策点切回 RuleOnly，通知 Agent 团队

## 7. 落地计划（四阶段）

### 阶段一：影子模式（第 1-2 周）
- 目标: 零风险引入，Agent 只观察不决策
- `DecisionPoint` 抽象落地到 1-2 个核心决策点
- Agent 集群最小部署（3 个 Warm Agent Pod + 1 Gateway）
- Shadow 模式运行，对比 Agent vs 规则决策
- 验收: 匹配率 > 85%，额外延迟 < 1ms，零业务影响，无内存泄漏

### 阶段二：单点灰度（第 3-4 周）
- 目标: 低风险决策点 Agent First，规则兜底
- 1 个低风险决策点切到 Agent First
- 安全护栏生效（硬约束校验）
- L1/L2 降级层部署 + 联调
- 验收: Agent 决策占比 > 95%，规则兜底 100% 命中，降级恢复链路验证

### 阶段三：关键路径 + 多 Agent 协作（第 5-8 周）
- 目标: 高风险决策点 + 编排/协商模式上线
- 风控 Agent 上线（< 10ms 超时）
- 编排决策上线（风控 + 反洗钱 + 设备风险 多 Agent 协作）
- L3-L5 降级层联调，NATS JetStream + Cold Path Worker Pool
- 验收: 风控 P99 < 15ms，编排成功率 > 95%，五层降级逐层触发验证，可用性 > 99.9%

### 阶段四：全面推广 + 自愈闭环（第 9-12 周）
- 目标: 运维自愈 Agent 上线，Agent 集群自身形成负反馈闭环
- 自愈 Agent（自动扩缩容、阈值自调优、Agent 替换）
- 覆盖所有决策点
- 验收: Agent 可用性 > 99.95%，人工介入 < 1 次/周

每个阶段可独立上线、可回滚。回滚方式: 关开关 / 切回 RuleOnly / 逐决策点回切 / 按层回滚。

## 8. 关键设计决策追溯

1. **为什么选独立 Agent 集群而非进程内嵌入？** — 用户已有多个业务系统，Agent 需要跨系统协作和独立扩缩。但 L0 Hot Path 保留进程内嵌入选项（SDK 模式）以支撑毫秒级决策。

2. **为什么分三层而非统一架构？** — 混合延迟要求（毫秒/百毫秒/秒）决定了统一的通信模式无法同时满足。分层后每层可以独立选型、独立扩缩、独立降级。

3. **为什么用 channel 而非 mutex？** — Go 的 channel 提供天然的 happens-before 保证和背压信号，channel buffer 满就是反压，select default 就是降级。Mutex 需要自己实现超时、队列、优先级等逻辑。

4. **为什么 NATS 而非 Kafka？** — NATS JetStream 部署更轻（单二进制），Go 原生客户端，push-based consumer 更适合 Agent Worker Pool 的消费模型。大规模场景可替换为 Kafka，接口层不绑定。

5. **为什么上下文传引用不传值？** — 50KB 上下文 Fan-Out 到 5 个子 Agent 全传 = 250KB 序列化开销。引用 + 按需字段 = 每个 Agent 只拿 2-5KB，节省 90%+。同时提供信息隔离（风控 Agent 不需要看 PII）。
