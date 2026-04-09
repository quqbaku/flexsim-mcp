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


# === 启动服务器 ===

if __name__ == "__main__":
    mcp.run()
