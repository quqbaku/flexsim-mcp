"""MCP 工具定义 - Phase 1 基础工具"""

from typing import Optional, Dict, Any
from .flexsim_client import get_client
from .session import get_session
from . import flexsim_builder
from .errors import ModelValidationError, ModelBuildError


def _tool_wrapper(func):
    """工具包装器：通过会话管理器串行化执行"""
    def wrapper(*args, **kwargs):
        session = get_session()
        return session.execute_with_client(func, *args, **kwargs)
    return wrapper


# === 连接控制 ===

@_tool_wrapper
def flexsim_launch(client) -> str:
    """启动 FlexSim 进程"""
    return client.launch()


@_tool_wrapper
def flexsim_connect(client) -> str:
    """连接到已运行的 FlexSim 实例"""
    return client.connect()


@_tool_wrapper
def flexsim_disconnect(client) -> str:
    """断开 FlexSim 连接"""
    return client.disconnect()


# === 模型操作 ===

@_tool_wrapper
def flexsim_open_model(client, path: str = "") -> str:
    """
    打开模型文件

    Args:
        path: 模型文件路径，为空则创建空白模型
    """
    return client.open_model(path)


@_tool_wrapper
def flexsim_reset(client) -> str:
    """重置仿真"""
    return client.reset()


# === 仿真控制 ===

@_tool_wrapper
def flexsim_run(client, speed: float = 1.0) -> str:
    """
    运行仿真

    Args:
        speed: 运行速度倍数
    """
    return client.run(speed)


@_tool_wrapper
def flexsim_run_to_time(client, time: float) -> str:
    """
    运行仿真到指定时间

    Args:
        time: 目标仿真时间
    """
    return client.run_to_time(time)


@_tool_wrapper
def flexsim_stop(client) -> str:
    """停止仿真"""
    return client.stop()


@_tool_wrapper
def flexsim_get_time(client) -> float:
    """获取当前仿真时间"""
    return client.get_time()


# === 参数管理 ===

@_tool_wrapper
def flexsim_get_parameter(client, name: str) -> float:
    """
    获取模型参数

    Args:
        name: 参数名称
    """
    return client.get_parameter(name)


@_tool_wrapper
def flexsim_set_parameter(client, name: str, value: float) -> str:
    """
    设置模型参数

    Args:
        name: 参数名称
        value: 参数值
    """
    return client.set_parameter(name, value)


@_tool_wrapper
def flexsim_get_performance_measure(client, name: str) -> float:
    """
    获取性能指标

    Args:
        name: 性能指标名称
    """
    return client.get_performance_measure(name)


# === 核心方法 ===

@_tool_wrapper
def flexsim_evaluate(client, expression: str) -> str:
    """
    执行任意 FlexScript 表达式（核心方法）

    Args:
        expression: FlexScript 表达式或语句
    """
    return client.evaluate(expression)


# === 模型查询 ===

@_tool_wrapper
def flexsim_get_model_tree(client) -> str:
    """获取模型中所有对象的树状结构"""
    script = """
    string s = "";
    for (int i = 1; i <= model().subnodes.length; i++) {
        Object obj = model().subnodes[i];
        s += "[" + i + "] " + obj.name + "\\n";
    }
    return s;
    """
    return client.evaluate(script)


@_tool_wrapper
def flexsim_get_object_info(client, name: str) -> str:
    """
    获取指定对象的信息

    Args:
        name: 对象名称
    """
    script = f"""
    Object obj = model().find("{name}");
    if (obj) {{
        return "名称: " + obj.name + ", 类型: " + obj.className;
    }}
    return "对象未找到: {name}";
    """
    return client.evaluate(script)


# === Phase 2：模型构建相关工具 ===


@_tool_wrapper
def flexsim_new_model(client, path: str = "") -> str:
    """创建空白模型或打开指定模型文件。"""
    # 复用现有 open_model 语义：空路径表示避免弹出对话框，继续当前模型。
    return client.open_model(path)


@_tool_wrapper
def flexsim_add_object(
    client,
    type: str,
    name: str,
    x: float,
    y: float,
    z: float,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """添加一个 3D 对象到模型并设置位置/部分参数。"""
    created = flexsim_builder.create_object(
        client.controller,
        type=type,
        name=name,
        x=x,
        y=y,
        z=z,
        params=params or {},
    )
    return {"ok": True, "object": created}


@_tool_wrapper
def flexsim_connect_objects(client, source: str, target: str) -> Dict[str, Any]:
    """连接两个对象的输出/输入端口。"""
    flexsim_builder.connect_objects(client.controller, source=source, target=target)
    return {"ok": True, "source": source, "target": target}


@_tool_wrapper
def flexsim_set_object_params(client, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """为指定对象设置一组参数/labels。"""
    flexsim_builder.apply_params(client.controller, name=name, params=params)
    return {"ok": True, "name": name}


@_tool_wrapper
def flexsim_validate_model(client) -> Dict[str, Any]:
    """验证当前模型的基本完整性。"""
    try:
        issues = flexsim_builder.validate_model(client.controller)
        return {"ok": True, "issues": issues}
    except ModelValidationError as exc:
        return {"ok": False, "error": str(exc)}


@_tool_wrapper
def flexsim_build_from_template(client, template_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """从预置模板快速构建模型。Phase 2 先仅支持 simple_production_line。"""
    if template_name != "simple_production_line":
        raise ModelBuildError(f"当前仅支持模板: simple_production_line，收到: {template_name}")

    # 非参数化的最小版本：Source -> Queue -> Processor -> Sink
    flexsim_builder.create_object(client.controller, type="Source", name="Source1", x=0, y=0, z=0, params=None)
    flexsim_builder.create_object(client.controller, type="Queue", name="Buffer", x=10, y=0, z=0, params=None)
    flexsim_builder.create_object(client.controller, type="Processor", name="Machine1", x=20, y=0, z=0, params=None)
    flexsim_builder.create_object(client.controller, type="Sink", name="Exit", x=30, y=0, z=0, params=None)

    flexsim_builder.connect_objects(client.controller, source="Source1", target="Buffer")
    flexsim_builder.connect_objects(client.controller, source="Buffer", target="Machine1")
    flexsim_builder.connect_objects(client.controller, source="Machine1", target="Exit")

    tree = flexsim_builder.get_model_tree(client.controller)
    return {"ok": True, "template": template_name, "objects": tree}
