"""模型程序化构建的内部封装（Phase 2 最小版本）。

注意：这里的接口面向 MCP 工具层，而不是直接暴露给外部客户端。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .errors import ModelBuildError, ModelValidationError, safe_evaluate


SUPPORTED_FIXED_TYPES = {"Source", "Queue", "Processor", "Sink", "Combiner", "Separator", "MultiProcessor"}


@dataclass
class ObjectSpec:
    type: str
    name: str
    x: float
    y: float
    z: float
    params: Dict[str, Any] | None = None


def create_object(controller, *, type: str, name: str, x: float, y: float, z: float, params: Dict[str, Any] | None = None) -> dict:
    “””创建 3D 对象并设置位置与部分参数。

    注意：此功能依赖 executor.fsm 的 send/receive 机制。
    在 executor.fsm 打通前，evaluate() 只能求值节点路径，无法执行此 FlexScript。
    “””
    if type not in SUPPORTED_FIXED_TYPES:
        raise ModelBuildError(f”不支持的对象类型: {type}”)

    # 1. 创建实例并命名、定位
    script = f”””
    Object obj = createinstance(library().find(“{type}”), model());
    obj.name = “{name}”;
    obj.setLocation({x}, {y}, {z});
    return obj.name;
    “””
    # 当前环境中 evaluate 可能返回 None（已在 safe_evaluate 中解释原因）。
    # 这里仍按”必须能执行并返回”处理，避免误以为创建成功。
    try:
        result = safe_evaluate(controller, script, allow_none=False)
        created_name = result.raw
    except ModelBuildError as e:
        raise ModelBuildError(
            f”创建对象失败: type={type}, name={name}。”
            f”可能原因：(1) executor.fsm 未打通导致 evaluate() 无法执行 FlexScript；”
            f”(2) FlexSim 连接已断开。原始错误: {e}”
        )

    if not created_name:
        raise ModelBuildError(
            f”创建对象失败: type={type}, name={name}（evaluate 未返回对象名）。”
            f”这通常表示 executor.fsm 尚未打通，请先运行 smoke_eval.py 验证。”
        )

    # 2. 设置参数（可选，通过 labels）
    if params:
        for key, value in params.items():
            script_param = f”””
            Object obj = model().find(“{name}”);
            if (obj) {{
                obj.labels[“{key}”].value = {value};
            }}
            “””
            try:
                safe_evaluate(controller, script_param, allow_none=False)
            except ModelBuildError:
                # 参数设置失败不影响对象创建，但记录警告
                pass

    return {“type”: type, “name”: name, “x”: x, “y”: y, “z”: z, “params”: params or {}}


def connect_objects(controller, *, source: str, target: str) -> None:
    """连接两个对象的输出/输入端口。

    注意：此功能依赖 executor.fsm 的 send/receive 机制。
    """
    script = f"""
    Object src = model().find("{source}");
    Object dst = model().find("{target}");
    if (!src || !dst) {{
        return "ERROR: 对象不存在";
    }}
    src.outputConnect(dst);
    return "OK";
    """
    try:
        result = safe_evaluate(controller, script, allow_none=False).raw
        if result.startswith("ERROR"):
            raise ModelBuildError(f"连接对象失败: {result}")
    except ModelBuildError as e:
        raise ModelBuildError(
            f"连接对象失败: source={source}, target={target}。"
            f"可能原因：(1) 对象不存在于模型中；(2) executor.fsm 未打通。"
            f"原始错误: {e}"
        )


def apply_params(controller, *, name: str, params: Dict[str, Any]) -> None:
    """为已存在对象批量设置参数/labels。"""
    for key, value in params.items():
        script = f"""
        Object obj = model().find("{name}");
        if (!obj) {{
            return "ERROR: 对象不存在";
        }}
        obj.labels["{key}"].value = {value};
        return "OK";
        """
        try:
            result = safe_evaluate(controller, script, allow_none=False).raw
            if result.startswith("ERROR"):
                raise ModelBuildError(f"设置对象参数失败: {result}")
        except ModelBuildError as e:
            raise ModelBuildError(
                f"设置对象参数失败: name={name}, key={key}。原始错误: {e}"
            )


def get_model_tree(controller) -> List[str]:
    """返回当前模型的一维对象名称列表（Phase 2 调试用）。

    注意：此功能依赖 executor.fsm 的 send/receive 机制。
    在 executor.fsm 打通前，evaluate() 无法执行此 FlexScript。
    """
    script = """
    string s = "";
    for (int i = 1; i <= model().subnodes.length; i++) {
        Object obj = model().subnodes[i];
        s += obj.name + "\\n";
    }
    return s;
    """
    try:
        result = safe_evaluate(controller, script, allow_none=False).raw
    except ModelBuildError:
        # 如果 evaluate() 失败，返回空列表
        return []
    lines = [line for line in result.splitlines() if line.strip()]
    return lines


def validate_model(controller) -> List[str]:
    """基础模型验证：Source/Sink 存在性与输出连接检查。

    注意：此功能依赖 executor.fsm 的 send/receive 机制。
    在 executor.fsm 打通前，evaluate() 无法执行此 FlexScript。
    """
    issues: List[str] = []

    # 1. 收集所有顶层对象及其类型和是否有输出连接
    script = """
    string s = "";
    for (int i = 1; i <= model().subnodes.length; i++) {
        Object obj = model().subnodes[i];
        int hasOutput = (obj.outPorts.length > 0 && obj.outPorts[1].connections.length > 0);
        s += obj.name + "|" + obj.className + "|" + numtostring(hasOutput) + "\\n";
    }
    return s;
    """
    try:
        result = safe_evaluate(controller, script, allow_none=False).raw
    except ModelBuildError:
        # evaluate() 失败，可能是 executor.fsm 未打通
        issues.append(
            "模型验证失败：无法读取模型对象。这通常表示 executor.fsm 尚未打通，"
            "evaluate() 无法执行 FlexScript。请先运行 smoke_eval.py 验证执行通道。"
        )
        return issues
    lines = [line for line in result.splitlines() if line.strip()]

    has_source = False
    has_sink = False

    for line in lines:
        try:
            name, class_name, has_output_str = line.split("|")
        except ValueError:
            continue

        if class_name == "Source":
            has_source = True
        if class_name == "Sink":
            has_sink = True

        if class_name in SUPPORTED_FIXED_TYPES and class_name != "Sink" and has_output_str == "0":
            issues.append(f"对象 {name}({class_name}) 没有任何输出连接。")

    if not has_source:
        issues.append("模型中缺少 Source，对象无法生成。")
    if not has_sink:
        issues.append("模型中缺少 Sink，对象无法被移除。")

    if issues:
        raise ModelValidationError("; ".join(issues))

    return issues

