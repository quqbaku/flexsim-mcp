# FlexSim MCP Server

通过 Model Context Protocol (MCP) 控制 FlexSim 仿真引擎，实现自然语言驱动的仿真建模与自动化。

> 本项目基于 [SethGame/mcp_flexsim](https://github.com/SethGame/mcp_flexsim) 扩展，核心增量：支持从自然语言描述自动生成 FlexSim 模型。

## 功能特性

- **MCP 协议接口**：通过标准 MCP 工具控制 FlexSim（启动、运行、停止、评估表达式）
- **模型操作**：打开模型、重置、运行到指定时间
- **FlexScript 集成**：通过 `evaluate()` 执行任意 FlexScript 表达式
- **会话管理**：线程安全的单例会话管理，支持并发调用

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
| `flexsim_evaluate` | 执行 FlexScript 表达式 |
| `flexsim_get_model_tree` | 获取模型对象树 |
| `flexsim_get_object_info` | 获取指定对象信息 |

## 示例用法

```
You: 启动 FlexSim
Claude: 调用 flexsim_launch

You: 打开模型 C:\Models\test.fsm
Claude: 调用 flexsim_open_model(path="C:\\Models\\test.fsm")

You: 运行仿真到 3600 秒
Claude: 调用 flexsim_run_to_time(time=3600)

You: 获取当前仿真时间
Claude: 调用 flexsim_get_time()

You: 执行 FlexScript 获取模型时间
Claude: 调用 flexsim_evaluate(expression="MAIN:/project/exec/time")
```

## 目录结构

```
flexsim-mcp/
├── mcp_server/              # MCP 服务器核心
│   ├── __init__.py
│   ├── server.py            # 服务器入口
│   ├── tools.py             # MCP 工具定义
│   ├── session.py           # 会话管理
│   └── flexsim_client.py    # FlexSimPy 封装
├── FlexSimPy-25.0.11/       # FlexSimPy SDK（子模块）
├── docs/                    # 项目文档
├── config.toml              # 配置文件
├── pyproject.toml           # Python 项目配置
├── requirements.txt         # 依赖列表
├── verify_stage1.py         # Phase 1 验收脚本
└── start_mcp.bat            # 启动脚本
```

## 验证

运行 Phase 1 验收脚本：

```bash
python verify_stage1.py
```

预期输出：`Result: PASS`

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

- [SethGame/mcp_flexsim](https://github.com/SethGame/mcp_flexsim) — 基础参考
- [FlexSim 官方文档](https://docs.flexsim.com/)
- [FastMCP 框架](https://github.com/jlowin/fastmcp)
- [MCP 协议规范](https://modelcontextprotocol.io)
