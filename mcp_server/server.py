"""MCP 服务器入口"""

from fastmcp import FastMCP

# 创建 FastMCP 实例
mcp = FastMCP("FlexSim MCP Server")

# 导入所有工具
from . import tools


# === 连接控制 ===

@mcp.tool()
def flexsim_launch() -> str:
    """启动 FlexSim 进程"""
    return tools.flexsim_launch()


@mcp.tool()
def flexsim_connect() -> str:
    """连接到已运行的 FlexSim 实例"""
    return tools.flexsim_connect()


@mcp.tool()
def flexsim_disconnect() -> str:
    """断开 FlexSim 连接"""
    return tools.flexsim_disconnect()


# === 模型操作 ===

@mcp.tool()
def flexsim_open_model(path: str = "") -> str:
    """
    打开模型文件

    Args:
        path: 模型文件路径，为空则创建空白模型
    """
    return tools.flexsim_open_model(path)


@mcp.tool()
def flexsim_reset() -> str:
    """重置仿真"""
    return tools.flexsim_reset()


# === 仿真控制 ===

@mcp.tool()
def flexsim_run(speed: float = 1.0) -> str:
    """
    运行仿真

    Args:
        speed: 运行速度倍数
    """
    return tools.flexsim_run(speed)


@mcp.tool()
def flexsim_run_to_time(time: float) -> str:
    """
    运行仿真到指定时间

    Args:
        time: 目标仿真时间
    """
    return tools.flexsim_run_to_time(time)


@mcp.tool()
def flexsim_stop() -> str:
    """停止仿真"""
    return tools.flexsim_stop()


@mcp.tool()
def flexsim_get_time() -> float:
    """获取当前仿真时间"""
    return tools.flexsim_get_time()


# === 参数管理 ===

@mcp.tool()
def flexsim_get_parameter(name: str) -> float:
    """
    获取模型参数

    Args:
        name: 参数名称
    """
    return tools.flexsim_get_parameter(name)


@mcp.tool()
def flexsim_set_parameter(name: str, value: float) -> str:
    """
    设置模型参数

    Args:
        name: 参数名称
        value: 参数值
    """
    return tools.flexsim_set_parameter(name, value)


@mcp.tool()
def flexsim_get_performance_measure(name: str) -> float:
    """
    获取性能指标

    Args:
        name: 性能指标名称
    """
    return tools.flexsim_get_performance_measure(name)


# === 核心方法 ===

@mcp.tool()
def flexsim_evaluate(expression: str) -> str:
    """
    执行任意 FlexScript 表达式（核心方法）

    Args:
        expression: FlexScript 表达式或语句
    """
    return tools.flexsim_evaluate(expression)


@mcp.tool()
def flexsim_execute_script(script: str, timeout: float = 5.0) -> str:
    """
    通过 send/receive 机制执行 FlexScript 代码（US-001 核心方法）。

    当 evaluate() 无法执行 FlexScript 时，使用此方法。
    它通过 executor.fsm 模型接收 FlexScript 字符串、执行并返回结果。

    Args:
        script: 要执行的 FlexScript 代码
        timeout: 超时时间（秒），默认 5 秒
    """
    return tools.flexsim_execute_script(script, timeout)


# === 模型查询 ===

@mcp.tool()
def flexsim_get_model_tree() -> str:
    """获取模型中所有对象的树状结构"""
    return tools.flexsim_get_model_tree()


@mcp.tool()
def flexsim_get_object_info(name: str) -> str:
    """
    获取指定对象的信息

    Args:
        name: 对象名称
    """
    return tools.flexsim_get_object_info(name)


# === Phase 2：模型构建 ===

@mcp.tool()
def flexsim_new_model(path: str = "") -> str:
    """创建空白模型或打开指定模型文件（Phase 2）。"""
    return tools.flexsim_new_model(path)


@mcp.tool()
def flexsim_add_object(
    type: str | None = None,
    name: str | None = None,
    x: float | str | None = None,
    y: float | str | None = None,
    z: float | str | None = None,
    params: dict | None = None,
    # 兼容常见别名
    object_type: str | None = None,
    objectType: str | None = None,
) -> dict:
    """添加对象到模型（Phase 2）。"""
    effective_type = type or object_type or objectType
    if effective_type is None:
        raise ValueError("缺少参数：type（或 object_type/objectType）")
    if name is None:
        raise ValueError("缺少参数：name")
    if x is None or y is None or z is None:
        raise ValueError("缺少参数：x/y/z")
    return tools.flexsim_add_object(
        type=effective_type,
        name=name,
        x=float(x),
        y=float(y),
        z=float(z),
        params=params,
    )


@mcp.tool()
def flexsim_connect_objects(source: str, target: str) -> dict:
    """连接两个对象（Phase 2）。"""
    return tools.flexsim_connect_objects(source=source, target=target)


@mcp.tool()
def flexsim_set_object_params(name: str, params: dict) -> dict:
    """设置对象参数/labels（Phase 2）。"""
    return tools.flexsim_set_object_params(name=name, params=params)


@mcp.tool()
def flexsim_validate_model() -> dict:
    """验证模型完整性（Phase 2）。"""
    return tools.flexsim_validate_model()


@mcp.tool()
def flexsim_build_from_template(
    template_name: str | None = None,
    params: dict | None = None,
    # 兼容部分客户端的 camelCase / 误传字段
    templateName: str | None = None,
    path: str | None = None,
) -> dict:
    """从预置模板构建模型（Phase 2）。"""
    _ = path  # 当前模板构建不使用路径参数，但允许客户端误传
    effective_name = template_name or templateName
    if not effective_name:
        # 让 MCP 层直接报错更清晰
        raise ValueError("缺少参数：template_name（或 templateName）")
    return tools.flexsim_build_from_template(template_name=effective_name, params=params)


# === 启动服务器 ===

if __name__ == "__main__":
    mcp.run()
