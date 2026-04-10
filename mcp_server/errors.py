"""Phase 2 通用异常与安全 evaluate 封装。"""

from __future__ import annotations

from dataclasses import dataclass


class FlexSimError(Exception):
    """与 FlexSim 交互时的通用异常基类。"""


class ModelBuildError(FlexSimError):
    """模型构建过程中出现的错误（脚本语法、对象不存在等）。"""

    def __init__(self, message: str, issues: list | None = None):
        super().__init__(message)
        self.issues = issues or []


class ModelValidationError(FlexSimError):
    """模型验证失败时抛出的异常。"""


@dataclass
class EvaluateResult:
    """封装 evaluate 调用的结果，便于后续扩展。"""

    raw: str


def safe_evaluate(controller, script: str, *, allow_none: bool = False) -> EvaluateResult:
    """安全执行 FlexScript / 节点表达式。

    - 捕获底层异常并转换为 ModelBuildError。
    - 对返回 None 的情况给出更友好的错误信息。
    """
    try:
        result = controller.evaluate(script)
    except Exception as exc:  # pragma: no cover - 具体异常类型由 FlexSimPy 决定
        raise ModelBuildError(f"FlexSim evaluate 调用失败: {exc}\n脚本片段: {script[:200]}") from exc

    if result is None:
        if allow_none:
            return EvaluateResult(raw="")
        raise ModelBuildError(
            "FlexSim evaluate 返回 None。当前环境下该通道似乎仅支持节点路径（例如 MAIN:/project/exec/time），"
            "不支持执行 FlexScript（例如 return time(); 或 createinstance(...)）。\n"
            f"脚本片段: {script[:200]}"
        )

    return EvaluateResult(raw=result)

