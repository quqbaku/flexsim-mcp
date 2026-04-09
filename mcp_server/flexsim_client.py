"""FlexSimPy 客户端封装 - 封装 FlexSimPy 的 12 个方法"""

import os
import sys
import tomllib
from pathlib import Path

# 懒加载 FlexSimPy
_flexsimpy = None


def _add_flexsim_to_path():
    """将 FlexSim 目录添加到 Python 路径和系统 PATH"""
    config_path = Path(__file__).parent.parent / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        program_dir = config.get("flexsim", {}).get("program_dir")
        if program_dir:
            # 添加到 Python 路径（用于导入 FlexSimPy）
            if program_dir not in sys.path:
                sys.path.insert(0, program_dir)
            # 添加到系统 PATH（用于 FlexSimPy.pyd 加载 flexsim.dll）
            flexsim_bin = Path(program_dir) / "program"
            if str(flexsim_bin) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(flexsim_bin) + os.pathsep + os.environ.get("PATH", "")


def _get_flexsimpy():
    """延迟导入 FlexSimPy"""
    global _flexsimpy
    if _flexsimpy is None:
        _add_flexsim_to_path()
        try:
            import FlexSimPy as _flexsimpy
        except ImportError as e:
            raise RuntimeError(
                f"无法导入 FlexSimPy，请确保已编译 FlexSimPy 模块并将其添加到 Python 路径。"
                f"错误: {e}"
            )
    return _flexsimpy


def _load_config():
    """加载 config.toml 配置"""
    config_path = Path(__file__).parent.parent / "config.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    with open(config_path, "rb") as f:
        return tomllib.load(f)


class FlexSimClient:
    """FlexSimPy 客户端封装"""

    def __init__(self):
        self._controller = None
        self._config = None

    @property
    def config(self):
        """懒加载配置"""
        if self._config is None:
            self._config = _load_config()
        return self._config

    @property
    def controller(self):
        """获取 controller（未启动时为 None）"""
        return self._controller

    @property
    def is_connected(self) -> bool:
        """检查是否已连接 FlexSim"""
        return self._controller is not None

    # === 连接控制 ===

    def launch(self) -> str:
        """启动 FlexSim 进程（fp.launch 是模块级函数，返回 Controller）"""
        flexsim_config = self.config["flexsim"]
        program_dir = flexsim_config.get("program_dir", "C:\\FlexSim")
        evaluation_license = flexsim_config.get("evaluation_license", True)
        show_gui = flexsim_config.get("show_gui", False)

        fp = _get_flexsimpy()
        self._controller = fp.launch(
            programDir=program_dir,
            evaluationLicense=evaluation_license,
            showGUI=show_gui
        )
        return f"FlexSim 已启动 (program_dir: {program_dir})"

    def connect(self) -> str:
        """连接到已运行的 FlexSim 实例"""
        if not self.is_connected:
            self.launch()
        return "已连接到 FlexSim"

    def disconnect(self) -> str:
        """断开连接"""
        self._controller = None
        return "已断开 FlexSim 连接"

    # === 模型操作 ===

    def open_model(self, path: str) -> str:
        """打开模型文件"""
        if not path:
            return "未指定模型路径：已跳过 open() 以避免文件选择框阻塞，请提供 .fsm 路径或继续使用当前模型"
        else:
            self.controller.open(path)
            return f"已打开模型: {path}"

    def reset(self) -> str:
        """重置仿真"""
        self.controller.reset()
        return "仿真已重置"

    # === 仿真控制 ===

    def run(self, speed: float = 1.0) -> str:
        """按速度运行仿真"""
        self.controller.run(speed)
        return f"仿真运行中 (速度: {speed}x)"

    def run_to_time(self, time: float) -> str:
        """运行到指定时间"""
        self.controller.runToTime(time)
        return f"仿真运行至时间: {time}"

    def stop(self) -> str:
        """停止仿真"""
        self.controller.stop()
        return "仿真已停止"

    def get_time(self) -> float:
        """获取当前仿真时间"""
        return self.controller.time()

    # === 参数管理 ===

    def get_parameter(self, name: str) -> float:
        """获取模型参数"""
        return self.controller.getParameter(name)

    def set_parameter(self, name: str, value: float) -> str:
        """设置模型参数"""
        self.controller.setParameter(name, value)
        return f"参数已设置: {name} = {value}"

    def get_performance_measure(self, name: str) -> float:
        """获取性能指标"""
        return self.controller.getPerformanceMeasure(name)

    # === 核心方法 ===

    def evaluate(self, expression: str) -> str:
        """执行任意 FlexScript 表达式（核心方法）"""
        result = self.controller.evaluate(expression)
        if result is None and "://" not in expression:
            raise RuntimeError(
                "FlexSimPy Controller.evaluate() 在当前 SDK 中接受的是节点路径，不是 FlexScript 代码。"
                "例如可用: MAIN:/project/exec/time"
            )
        return result if result is not None else ""

    # === 消息传递 ===

    def send(self, message: str) -> str:
        """发送消息到 FlexSim"""
        self.controller.send(message)
        return f"消息已发送: {message}"

    def receive(self) -> str:
        """接收来自 FlexSim 的消息"""
        return self.controller.receive() or ""


# 单例全局客户端
_client = None


def get_client() -> FlexSimClient:
    """获取全局 FlexSim 客户端实例"""
    global _client
    if _client is None:
        _client = FlexSimClient()
    return _client
