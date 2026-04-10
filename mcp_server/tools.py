"""MCP 工具定义 - Phase 1 基础工具"""

from typing import Optional, Dict, Any
from .flexsim_client import get_client
from .session import get_session
from . import flexsim_builder
from . import translator as spec_translator
from . import model_spec
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


@_tool_wrapper
def flexsim_execute_script(client, script: str, timeout: float = 5.0) -> str:
    """
    通过 send/receive 机制执行 FlexScript 代码（US-001 核心方法）。

    当 evaluate() 无法执行 FlexScript 时，使用此方法。
    它通过 executor.fsm 模型接收 FlexScript 字符串、执行并返回结果。

    Args:
        script: 要执行的 FlexScript 代码
        timeout: 超时时间（秒），默认 5 秒
    """
    return client.execute_script(script, timeout)


# === 模型查询 ===

@_tool_wrapper
def flexsim_get_model_tree(client, detail_level: str = "basic") -> str:
    """
    获取模型中所有对象的树状结构

    Args:
        detail_level: 'basic' 返回名称列表（每行一个），'full' 返回含类型和坐标的 JSON
    """
    if detail_level == "basic":
        script = """
        string s = "";
        for (int i = 1; i <= model().subnodes.length; i++) {
            Object obj = model().subnodes[i];
            s += "[" + i + "] " + obj.name + "\\n";
        }
        return s;
        """
        return client.evaluate(script)
    elif detail_level == "full":
        script = """
        string s = "[";
        for (int i = 1; i <= model().subnodes.length; i++) {
            Object obj = model().subnodes[i];
            if (i > 1) s += ",";
            s += "{\\"name\\":\\"" + obj.name + "\\",\\"type\\":\\"" + obj.className + "\\",";
            s += "\\"x\\":" + numtostring(obj.x) + ",";
            s += "\\"y\\":" + numtostring(obj.y) + ",";
            s += "\\"z\\":" + numtostring(obj.z) + "}";
        }
        s += "]";
        return s;
        """
        return client.evaluate(script)
    else:
        raise ValueError(f"detail_level must be 'basic' or 'full', got: {detail_level}")


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
def flexsim_new_model(client) -> dict:
    """
    创建空白模型（US-003）。

    内部调用 client.new_model() 创建全新的空 FlexSim 模型，
    如果 executor.fsm 之前已加载则重新加载以维持执行通道。

    Returns:
        dict: 包含 'ok'、'message'（成功确认消息）和 'object_count'（模型对象数量）
    """
    return client.new_model()


@_tool_wrapper
def flexsim_add_object(
    client,
    type: str,
    name: str,
    x: float,
    y: float,
    z: float,
    params: Optional[Dict[str, Any]] = None,
    object_type: Optional[str] = None,
    objectType: Optional[str] = None,
) -> Dict[str, Any]:
    """添加一个 3D 对象到模型并设置位置/部分参数。

    Args:
        type: 对象类型（支持 'Source', 'Queue', 'Processor', 'Sink' 等）
        name: 对象名称
        x, y, z: 位置坐标（支持字符串或数字）
        params: 可选参数字典
        object_type, objectType: type 的别名，兼容不同命名风格
    """
    # 兼容 type/object_type/objectType 不同命名
    obj_type = type or object_type or objectType
    # 兼容字符串和数字坐标
    x_val = float(x) if isinstance(x, (int, str)) else x
    y_val = float(y) if isinstance(y, (int, str)) else y
    z_val = float(z) if isinstance(z, (int, str)) else z

    created = flexsim_builder.create_object(
        client.controller,
        type=obj_type,
        name=name,
        x=x_val,
        y=y_val,
        z=z_val,
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


@_tool_wrapper
def flexsim_build_from_spec(client, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    根据 ModelSpec JSON 构建自定义仿真模型（US-007）。

    传入完整的 ModelSpec JSON，内部自动完成：
    1. 解析 JSON 为 ModelSpec 对象
    2. 校验 ModelSpec 结构（通过 validate_model_spec）
    3. 调用 ModelSpecTranslator.translate() 创建对象和连接

    Args:
        spec: ModelSpec 字典，包含 model_name, objects, connections, simulation

    Returns:
        dict: 包含 'ok' 和 'message'（成功消息或错误信息）
              如果校验失败，返回 {'ok': False, 'error': '...', 'issues': [...]}
    """
    try:
        # 1. 解析 JSON 为 ModelSpec
        model_spec_obj = model_spec.parse_model_spec(spec)

        # 2. 翻译并构建（内部会校验）
        translator = spec_translator.ModelSpecTranslator()
        translator.translate(model_spec_obj, client.controller)

        # 3. 返回成功信息
        object_count = len(model_spec_obj.objects)
        connection_count = len(model_spec_obj.connections)
        return {
            "ok": True,
            "message": f"模型已构建：{object_count} 个对象，{connection_count} 条连接",
            "objects": object_count,
            "connections": connection_count,
        }
    except ModelBuildError as e:
        # 校验失败 - issues 来自 validate_model_spec
        return {"ok": False, "error": str(e), "issues": e.issues}
    except Exception as e:
        return {"ok": False, "error": f"构建失败: {e}", "issues": []}
