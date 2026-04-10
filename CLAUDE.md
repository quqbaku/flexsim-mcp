# flexsim-mcp - 团队运营手册

> 由 team-project-setup 自动生成，可按需修改。
> 此文件让 team-lead 的团队知识在上下文压缩后仍然保持。

## Team-Lead 控制平面

- team-lead = 主对话，不是生成的 agent
- team-lead 负责用户对齐、范围控制、任务分解和阶段推进
- team-lead 维护项目全局真相：主 `task_plan.md`、`decisions.md` 和此 `CLAUDE.md`
- team-lead 决定某个流程改进是项目本地的还是需要写回 `CCteam-creator` 的
- **禁用独立子智能体**：团队存在后，所有工作通过 SendMessage 交给队友。不要启动独立的 Agent/子智能体（Explore、general-purpose 等）——它们绕过团队的规划文件和协作体系。唯一例外：用 `team_name` 生成新队友加入团队

## 团队花名册

| 名称 | 角色 | 模型 | 核心能力 |
|------|------|------|---------|
| backend-dev | 后端开发 | sonnet | FlexScript 执行通道 + Phase 2 工具链实现 |
| researcher | 探索/研究 | sonnet | FlexSim/FlexScript API 调研 |
| reviewer | 代码审查 | sonnet | 安全/质量/性能审查（只读） |

## 任务下发协议

### TaskCreate 描述格式（team-lead 上下文压缩后参考）

TaskCreate 描述：一句话范围 + 验收标准 + `.plans/` 路径。
通过 TaskUpdate 分配负责人和设置依赖。

### 大任务（功能开发、新模块）-- 停止检查后再发送

**在给任何智能体下发大任务前，检查消息中是否包含以下 4 项。如有缺失，先补上再发。**

1. **范围和目标**：要做什么、验收标准
2. **文档提醒**："请创建 `<前缀>-<任务名>/` 任务文件夹（含 task_plan.md + findings.md + progress.md），并在你的根 findings.md 中添加索引条目"
3. **依赖说明**：依赖哪些调研/任务的结论，关键文件路径和行号
4. **审查预期**：完成后是否需要代码审查

### 小任务（Bug 修复、配置变更）

直接发消息说明改动即可，不需要任务文件夹，也不需要审查。

## 通信速查

| 操作 | 命令 |
|------|------|
| 给单个智能体分配任务 | `SendMessage(to: "<名称>", message: "...")` |
| 广播给所有人（慎用） | `SendMessage(to: "*", message: "...")` |
| dev 请求代码审查 | dev 直接联系 reviewer（不经过 team-lead） |

## 状态检查

| 要检查什么 | 怎么做 |
|-----------|--------|
| 全局概览 | `TaskList` — 所有任务、负责人、阻塞情况一览 |
| 快速扫描 | 并行读取各 agent 的 `progress.md` |
| 深入了解 | 读 agent 的 `findings.md`（索引）→ 再看具体任务文件夹 |
| 方向检查 | 读 `.plans/flexsim-mcp/task_plan.md` |

读取顺序：**progress**（到哪了）→ **findings**（遇到什么）→ **task_plan**（目标是什么）

## 文档索引（知识库）

| 文档 | 位置 | 维护者 |
|------|------|--------|
| 导航地图 | .plans/flexsim-mcp/docs/index.md | team-lead |
| 架构 | .plans/flexsim-mcp/docs/architecture.md | team-lead, backend-dev |
| API 契约 | .plans/flexsim-mcp/docs/api-contracts.md | backend-dev（API 变更时必须同步） |
| 不变量 | .plans/flexsim-mcp/docs/invariants.md | team-lead, reviewer |

## 审查维度

> 项目特定的审查维度。Reviewer 在每次审查时给各维度打分。

| # | 维度 | 权重 | STRONG 表现 | WEAK 表现 |
|---|------|------|-----------|---------|
| RD-1 | 实际可用性 | 高 | 代码能真正打通 FlexScript 执行通道，Phase 2 工具链端到端可用 | 代码看起来对但实际跑不通，或只能走 Happy Path |
| RD-2 | 错误处理 | 中 | 所有边界情况有明确错误返回，错误信息可帮助调试 | 错误被吞掉或返回无意义的 None |
| RD-3 | API 设计 | 中 | 接口签名清晰，参数校验严格，返回值类型一致 | 参数任意传递都能"成功"，返回类型混乱 |

## 核心协议

| 协议 | 触发时机 | 操作 |
|------|---------|------|
| 需求对齐 | 团队搭建后、开发前 | researcher 探索代码库，team-lead 与用户对齐需求 |
| 3-Strike 上报 | 智能体报告 3 次失败 | 读其 progress.md，给新方向或重新分配 |
| 代码审查 | 大功能/新模块完成 | dev 在 findings.md 写改动摘要，发给 reviewer |
| 阶段推进 | 阶段完成 | 调研完：读 findings 更新主计划。开发完：等 reviewer [OK]/[WARN] |

## Known Pitfalls

（初始为空——从 3-Strike 解决方案、reviewer [BLOCK] 修复或任何重复失败中添加条目）

## 风格决策

（初始为空——根据用户反馈和审查发现填充）
