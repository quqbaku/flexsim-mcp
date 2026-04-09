# FlexSim MCP Server

通过 Model Context Protocol (MCP) 控制 FlexSim 仿真引擎，实现自然语言驱动的仿真建模与自动化。

> **Phase 2 状态（2026-04-09）**：建模工具层已完成，US-003（flexsim_new_model）和 US-006（ModelSpec 校验）已通过验收。FlexScript 执行通道（US-001/002）因 FlexSimPy SDK 限制暂时阻塞，需手动创建 `executor.fsm`（参考 `docs/executor-fsm-guide.md`）。

## 功能特性

### Phase 1（已完成）
- **MCP 协议接口**：通过标准 MCP 工具控制 FlexSim（启动、运行、停止、评估表达式）
- **模型操作**：打开模型、重置、运行到指定时间
- **FlexScript 集成**：通过 `evaluate()` 执行节点路径表达式
- **会话管理**：线程安全的单例会话管理，支持并发调用

### Phase 2（建模层，部分完成）
- **程序化建模**：`flexsim_new_model`、`flexsim_add_object`、`flexsim_connect_objects`
- **ModelSpec 校验**：JSON Schema 结构校验 + 7种对象类型白名单 + 拓扑完整性验证
- **模板构建**：`flexsim_build_from_template` 一键生成标准生产线模型
- **错误处理体系**：统一异常类型、安全求值封装、详细错误 JSON 响应
- **FlexScript 执行通道**：`flexsim_execute_script`（send/receive 包装，待 executor.fsm）

## 系统要求

- Windows 10/11
- FlexSim 2026 或更高版本
- Python 3.9 / 3.10 / 3.11 / 3.12
- 已编译的 FlexSimPy 扩展

## 快速开始

### 1. 配置

编辑 `config.toml`：

```toml
[flexsim]
program_dir = "C:\\Program Files\\FlexSim 2026"
evaluation_license = true
show_gui = false
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 MCP 服务器

```bash
# 方式一：直接运行
python -m mcp_server.server

# 方式二：使用启动脚本
.\start_mcp.bat
```

### 4. 在 Claude Code 中使用

在 `~/.claude.json` 中添加：

```json
{
  "mcpServers": {
    "flexsim": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "PYTHONPATH": "c:\\Users\\85273\\Desktop\\flexsim-mcp"
      },
      "cwd": "c:\\Users\\85273\\Desktop\\flexsim-mcp",
      "type": "stdio"
    }
  }
}
```

重启 Claude Code 后，用 `/mcp` 查看连接状态。

## MCP 工具列表

### 连接控制

| 工具 | 描述 |
|------|------|
| `flexsim_launch` | 启动 FlexSim 进程 |
| `flexsim_connect` | 连接到已运行的 FlexSim 实例 |
| `flexsim_disconnect` | 断开连接 |

### 模型操作

| 工具 | 描述 |
|------|------|
| `flexsim_open_model` | 打开模型文件（空路径创建空白模型） |
| `flexsim_reset` | 重置仿真 |

### 仿真控制

| 工具 | 描述 |
|------|------|
| `flexsim_run` | 按速度倍数运行仿真 |
| `flexsim_run_to_time` | 运行到指定仿真时间 |
| `flexsim_stop` | 停止仿真 |
| `flexsim_get_time` | 获取当前仿真时间 |

### 参数管理

| 工具 | 描述 |
|------|------|
| `flexsim_get_parameter` | 获取模型参数 |
| `flexsim_set_parameter` | 设置模型参数 |
| `flexsim_get_performance_measure` | 获取性能指标 |

### 核心方法

| 工具 | 描述 |
|------|------|
| `flexsim_evaluate` | 执行 FlexScript 表达式（节点路径） |
| `flexsim_get_model_tree` | 获取模型对象树（`detail_level=basic/full`） |
| `flexsim_get_object_info` | 获取指定对象信息 |

### Phase 2 建模工具

| 工具 | 描述 | 状态 |
|------|------|------|
| `flexsim_new_model` | 创建干净空模型 | ✅ 可用 |
| `flexsim_add_object` | 在模型中添加仿真对象 | 🔧 依赖 FlexScript 通道 |
| `flexsim_connect_objects` | 连接两个对象的端口 | 🔧 依赖 FlexScript 通道 |
| `flexsim_set_object_params` | 设置对象参数 | 🔧 依赖 FlexScript 通道 |
| `flexsim_validate_model` | 验证模型结构完整性 | ✅ 可用 |
| `flexsim_build_from_template` | 从模板快速创建标准模型 | 🔧 依赖 FlexScript 通道 |
| `flexsim_execute_script` | 执行任意 FlexScript 脚本 | ⏳ 待 executor.fsm |

## 示例用法

```
You: 启动 FlexSim
Claude: 调用 flexsim_launch

You: 创建一个新的空白模型
Claude: 调用 flexsim_new_model()

You: 打开模型 C:\Models\test.fsm
Claude: 调用 flexsim_open_model(path="C:\\Models\\test.fsm")

You: 运行仿真到 3600 秒
Claude: 调用 flexsim_run_to_time(time=3600)

You: 获取仿真时间节点值
Claude: 调用 flexsim_evaluate(expression="MAIN:/project/exec/time")

You: 校验 ModelSpec JSON 规格
Claude: 调用 flexsim_validate_model(spec={...})
```

## 目录结构

```
flexsim-mcp/
├── mcp_server/              # MCP 服务器核心
│   ├── server.py            # 服务器入口（工具注册）
│   ├── tools.py             # 所有 MCP 工具实现
│   ├── flexsim_client.py    # FlexSimPy 封装
│   ├── flexsim_builder.py   # Phase 2 建模操作
│   ├── model_spec.py        # ModelSpec 数据结构与校验
│   ├── translator.py        # spec → 建模指令翻译器
│   ├── errors.py            # 统一异常类型
│   └── session.py           # 会话管理
├── FlexSimPy-25.0.11/       # FlexSimPy SDK
├── docs/                    # 项目文档
│   ├── 阶段2进度交接.md      # Phase 2 详细交接文档
│   ├── executor-fsm-guide.md # 手动创建 executor.fsm 指引
│   └── 项目计划大纲.md
├── scripts/
│   ├── smoke_eval.py        # 结构化冒烟测试
│   └── ralph/               # Ralph AI 自动化任务文件
├── config.toml              # 配置文件
├── requirements.txt         # 依赖列表
├── verify_stage1.py         # Phase 1 验收脚本
└── start_mcp.bat            # 启动脚本
```

## 验证

```bash
# Phase 1 验收
python verify_stage1.py

# Phase 2 冒烟测试
python scripts/smoke_eval.py

# 官方 FlexSimPy 连通性测试
cd FlexSimPy-25.0.11/TestFlexSimPy
python TestFlexSimPy.py
```

## 已知问题

- **FlexScript 执行通道**：`flexsim_evaluate("return time();")` 在无 GUI 模式下返回 `None`（FlexSimPy SDK 限制）。建模工具（add/connect/build）依赖此通道，当前暂时阻塞。
- **解决路径**：使用 FlexSim GUI 手动创建 `executor.fsm`，参考 `docs/executor-fsm-guide.md`。

## 已知限制

- **仅限 Windows**：FlexSimPy 是 Windows `.pyd` 扩展
- **`evaluate()` 语义**：当前 SDK 的 `evaluate()` 执行节点路径求值，不是任意 FlexScript 代码
- **需要许可证**：开发测试可使用 `evaluation_license = true`

## 项目阶段

- **Phase 1** ✅：基础 MCP 服务器搭建完成
- **Phase 2**：模型程序化构建能力（规划中）
- **Phase 3**：AI 驱动的自然语言建模（规划中）
- **Phase 4**：批量实验与优化分析（规划中）

## 参考资源

- [FlexSim 官方文档](https://docs.flexsim.com/)
- [FastMCP 框架](https://github.com/jlowin/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
