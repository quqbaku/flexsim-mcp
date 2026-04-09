"""ModelSpec → FlexSim 构建翻译器（Phase 2 最小版本）。"""

from __future__ import annotations

from . import flexsim_builder
from .errors import ModelBuildError
from .model_spec import ModelSpec


class ModelSpecTranslator:
    """将精简版 ModelSpec 翻译为 builder 调用。

    Phase 2 仅要求支持 simple_production_line 这类线性拓扑。
    """

    def translate(self, spec: ModelSpec, controller) -> None:
        from .model_spec import validate_model_spec

        # 1. 先做结构层面的 JSON/ModelSpec 校验
        issues = validate_model_spec(spec)
        if issues:
            raise ModelBuildError("; ".join(issues))

        # 2. 创建对象
        for obj in spec.objects:
            flexsim_builder.create_object(
                controller,
                type=obj.type,
                name=obj.name,
                x=obj.x,
                y=obj.y,
                z=obj.z,
                params=obj.params,
            )

        # 3. 创建连接
        for conn in spec.connections:
            flexsim_builder.connect_objects(
                controller,
                source=conn.source,
                target=conn.target,
            )

