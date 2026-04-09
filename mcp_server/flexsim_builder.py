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
    """创建 3D 对象并设置位置与部分参数。"""
    if type not in SUPPORTED_FIXED_TYPES:
        raise ModelBuildError(f"不支持的对象类型: {type}")

    # 1. 创建实例并命名、定位
    script = f"""
    Object obj = createinstance(library().find("{type}"), model());
    obj.name = "{name}";
    obj.setLocation({x}, {y}, {z});
    return obj.name;
    """
    # 当前环境中 evaluate 可能返回 None（已在 safe_evaluate 中解释原因）。
    # 这里仍按“必须能执行并返回”处理，避免误以为创建成功。
    result = safe_evaluate(controller, script, allow_none=False)
    created_name = result.raw
    if not created_name:
        raise ModelBuildError(f"创建对象失败: type={type}, name={name}（evaluate 未返回对象名）")

    # 2. 设置参数（可选，通过 labels）
    if params:
        for key, value in params.items():
            # 这里直接写入 label 文本值，具体分布函数/表达式由上层保证合法
            script_param = f"""
            Object obj = model().find("{name}");
            if (obj) {{
                obj.labels["{key}"].value = {value};
            }}
            """
            safe_evaluate(controller, script_param, allow_none=False)

    return {"type": type, "name": name, "x": x, "y": y, "z": z, "params": params or {}}


def connect_objects(controller, *, source: str, target: str) -> None:
    """连接两个对象的输出/输入端口。"""
    script = f"""
    Object src = model().find("{source}");
    Object dst = model().find("{target}");
    if (!src || !dst) {{
        return "ERROR: 对象不存在";
    }}
    src.outputConnect(dst);
    return "OK";
    """
    result = safe_evaluate(controller, script, allow_none=False).raw
    if result.startswith("ERROR"):
        raise ModelBuildError(f"连接对象失败: {result}")


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
        result = safe_evaluate(controller, script, allow_none=False).raw
        if result.startswith("ERROR"):
            raise ModelBuildError(f"设置对象参数失败: {result}")


def get_model_tree(controller) -> List[str]:
    """返回当前模型的一维对象名称列表（Phase 2 调试用）。"""
    script = """
    string s = "";
    for (int i = 1; i <= model().subnodes.length; i++) {
        Object obj = model().subnodes[i];
        s += obj.name + "\\n";
    }
    return s;
    """
    result = safe_evaluate(controller, script, allow_none=False).raw
    lines = [line for line in result.splitlines() if line.strip()]
    return lines


def validate_model(controller) -> List[str]:
    """基础模型验证：Source/Sink 存在性与输出连接检查。"""
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
    result = safe_evaluate(controller, script, allow_none=False).raw
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

