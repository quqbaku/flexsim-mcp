"""Phase 2 精简版 ModelSpec 结构与校验。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

SUPPORTED_TYPES = {"Source", "Queue", "Processor", "Sink", "Combiner", "Separator", "MultiProcessor"}


@dataclass
class ObjectDef:
    type: str
    name: str
    x: float
    y: float
    z: float
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionDef:
    source: str
    target: str


@dataclass
class SimulationConfig:
    run_time: float


@dataclass
class ModelSpec:
    model_name: str
    objects: List[ObjectDef]
    connections: List[ConnectionDef]
    simulation: SimulationConfig


def _ensure(condition: bool, message: str, issues: List[str]) -> None:
    if not condition:
        issues.append(message)


def parse_model_spec(data: Dict[str, Any]) -> ModelSpec:
    """从 dict 解析为 ModelSpec，对键名做最小转换。"""
    objects = [
        ObjectDef(
            type=o["type"],
            name=o["name"],
            x=float(o["x"]),
            y=float(o["y"]),
            z=float(o.get("z", 0.0)),
            params=dict(o.get("params") or {}),
        )
        for o in data.get("objects", [])
    ]
    connections = [
        ConnectionDef(source=c["from"], target=c["to"])
        for c in data.get("connections", [])
    ]
    sim_conf_raw = data.get("simulation") or {}
    simulation = SimulationConfig(run_time=float(sim_conf_raw.get("runTime", 0.0)))
    return ModelSpec(
        model_name=data.get("model_name", "unnamed_model"),
        objects=objects,
        connections=connections,
        simulation=simulation,
    )


def validate_model_spec(spec: ModelSpec) -> List[str]:
    """校验 ModelSpec，返回问题列表（空列表表示校验通过）。"""
    issues: List[str] = []

    _ensure(bool(spec.objects), "objects 列表不能为空。", issues)
    _ensure(spec.simulation.run_time > 0, "simulation.runTime 必须为正数。", issues)

    name_set = {obj.name for obj in spec.objects}
    name_count: Dict[str, int] = {}

    for obj in spec.objects:
        _ensure(obj.type in SUPPORTED_TYPES, f"不支持的对象类型: {obj.type}", issues)
        _ensure(bool(obj.name), "对象 name 不能为空。", issues)

        # 统计名称出现次数，检测重复
        name_count[obj.name] = name_count.get(obj.name, 0) + 1

        # 校验坐标范围（FlexSim 模型有效范围约 -10000 到 10000）
        _ensure(-10000 <= obj.x <= 10000, f"对象 {obj.name} 的 x 坐标 {obj.x} 超出合理范围。", issues)
        _ensure(-10000 <= obj.y <= 10000, f"对象 {obj.name} 的 y 坐标 {obj.y} 超出合理范围。", issues)
        _ensure(-10000 <= obj.z <= 10000, f"对象 {obj.name} 的 z 坐标 {obj.z} 超出合理范围。", issues)

    # 检测重复名称
    for name, count in name_count.items():
        if count > 1:
            issues.append(f"对象名称重复: {name} (出现 {count} 次)。")

    for conn in spec.connections:
        _ensure(conn.source in name_set, f"连接 from={conn.source} 未在 objects 中定义。", issues)
        _ensure(conn.target in name_set, f"连接 to={conn.target} 未在 objects 中定义。", issues)
        _ensure(conn.source != conn.target, f"不允许自连接: {conn.source}。", issues)

    has_source = any(o.type == "Source" for o in spec.objects)
    has_sink = any(o.type == "Sink" for o in spec.objects)
    _ensure(has_source, "ModelSpec 中至少需要一个 Source。", issues)
    _ensure(has_sink, "ModelSpec 中至少需要一个 Sink。", issues)

    # 检测孤立对象（没有任何连接）
    connected_objects = set()
    for conn in spec.connections:
        connected_objects.add(conn.source)
        connected_objects.add(conn.target)

    for obj in spec.objects:
        if obj.name not in connected_objects and len(spec.connections) > 0:
            issues.append(f"对象 {obj.name} 没有任何连接，可能是孤立对象。")

    return issues

