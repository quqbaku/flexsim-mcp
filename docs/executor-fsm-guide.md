# executor.fsm 执行器模型说明

## 概述

`executor.fsm` 是 FlexSim MCP 项目的核心组件，用于解决 `controller.evaluate()` 无法执行任意 FlexScript 的问题。

## 问题背景

FlexSimPy SDK 的 `controller.evaluate()` 方法在当前环境下只能做"节点路径求值"（如 `MAIN:/project/exec/time`），无法执行任意 FlexScript 代码（如 `return time();`、`createinstance(...)`）。

## 解决方案

利用 FlexSim 的 `send/receive` 消息传递机制：

```
Python 端                          FlexSim 端 (executor.fsm)
-----------                        -----------------------
1. controller.send(flexscript)  →  接收消息
2.                               ←  execute_script() 执行
3. controller.receive()         ←  sendToController(result) 发送结果
```

## executor.fsm 模型结构

executor.fsm 包含一个 `FlexScriptExecutor` 对象，该对象具有：

- **类型**: BasicFR（基础固定资源）
- **位置**: (1000, 1000, 0) - 视窗之外，避免干扰
- **触发器**: OnMessage 触发器

### OnMessage 触发器代码

```flexscript
// OnMessage 触发器代码
// parstr(1) 包含发送的消息内容（FlexScript 代码）

string flexscriptCode = parstr(1);

// 执行 FlexScript 并获取结果
Variant result = evaluate(flexscriptCode);

// 将结果发送回调用者
sendToController(result);

return 1;
```

## 创建 executor.fsm

当前仓库环境下，`create_executor_model.py` 已可用于探测启动链路，但**还不能稳定生成可用的 `executor.fsm`**。因此这里的推荐路线已经改为：**优先手工创建，脚本仅用于调试，不作为主流程。**

### 最短手工步骤

1. 打开 FlexSim 2026 GUI。
2. 新建空模型。
3. 从 3D Library 拖一个 `BasicFR` 到模型里。
4. 重命名为 `FlexScriptExecutor`。
5. 将对象移动到视野外，例如 `(1000, 1000, 0)`。
6. 给该对象添加 `OnMessage` 触发器。
7. 将下面代码完整粘贴到 `OnMessage`：

```flexscript
string flexscriptCode = parstr(1);
Variant result = evaluate(flexscriptCode);
sendToController(result);
return 1;
```

8. 保存到项目根目录，文件名固定为 `executor.fsm`。

### 验证创建成功

在项目根目录执行：

```bash
python scripts/smoke_eval.py
```

至少应满足：

1. 不再出现 `executor.fsm 未找到`
2. `execute_script("return time();")` 返回非空结果
3. `execute_script("createinstance(library().find('Source'), model()); return 'ok';")` 返回 `ok`

### 脚本创建的当前状态

- `create_executor_model.py` 现在主要用于验证启动链路和环境配置。
- 它在当前环境下仍可能出现：启动成功，但 `evaluate()` 返回空结果、对象未真正创建、模型未保存。
- 因此，**不要把“脚本跑完”当成 executor 已创建成功的依据**，必须以根目录 `executor.fsm` 实际存在且 `smoke_eval.py` 通过为准。

## 使用 executor.fsm

### Python 端代码

```python
from mcp_server.flexsim_client import get_client

client = get_client()
client.launch()

# 加载执行器模型（首次自动加载）
client.execute_script("return time();")

# 或手动加载
client.load_executor()
result = client.execute_script("return 42;")
print(result)  # 输出: 42
```

### MCP 工具调用

```python
# 通过 MCP 服务器调用
result = mcp_server.tools.flexsim_execute_script("return time();")
```

## 工作原理详解

### 1. 消息发送 (Python → FlexSim)

```python
controller.send(flexscript_code)
```

FlexSimPy 内部调用 `sendToController()`，将消息放入队列。

### 2. 消息接收 (FlexSim 触发器)

FlexSim 的 OnMessage 触发器被激活：
- `parstr(1)` 获取消息内容（FlexScript 代码）
- `evaluate()` 执行代码
- `sendToController()` 将结果发回

### 3. 结果接收 (Python ← FlexSim)

```python
result = controller.receive()
```

FlexSimPy 内部调用 `receiveFromController()`，从队列获取结果。

### 4. 超时处理

`execute_script()` 方法实现了带超时的接收：
- 默认超时：5 秒
- 超时后抛出 `FlexSimError`

## 文件位置

- **executor.fsm**: 项目根目录 (`flexsim-mcp/executor.fsm`)
- **创建脚本**: `flexsim-mcp/create_executor_model.py`

## 故障排除

### executor.fsm 未找到

```
FlexSimError: executor.fsm 未找到。请先运行 create_executor_model.py 创建执行器模型。
```

**解决**: 优先按本文档的手工步骤在 FlexSim GUI 中创建 `executor.fsm`。

### 接收超时

```
FlexSimError: 接收 FlexScript 执行结果超时（5秒）
```

**可能原因**:
1. executor.fsm 未正确配置 OnMessage 触发器
2. FlexScript 执行时间过长
3. FlexSim 未正常运行

**解决**:
1. 重新运行 `create_executor_model.py`
2. 增加超时时间：`execute_script(script, timeout=30)`

### evaluate 返回 None 或空字符串

这是当前环境下的已知现象。`executor.fsm` 的存在正是为了解决这个问题。

使用 `execute_script()` 而非 `evaluate()` 来执行 FlexScript。

## 验收标准

- [ ] executor.fsm 文件创建成功
- [ ] executor.fsm 可通过 `controller.open('executor.fsm')` 加载
- [ ] executor.fsm 内含 OnMessage 触发器
- [ ] `execute_script("return time();")` 返回非空字符串
- [ ] `execute_script("createinstance(library().find('Source'), model()); return 'ok';")` 返回 `'ok'`
- [x] 提供本文档说明制作过程