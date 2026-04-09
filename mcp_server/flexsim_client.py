"""FlexSimPy 客户端封装 - 封装 FlexSimPy 的 12 个方法"""

import os
import sys
import tomllib
import threading
import time
from pathlib import Path

from .errors import safe_evaluate, ModelBuildError, FlexSimError

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


def _find_executor_model():
    """查找 executor.fsm 模型路径"""
    # 首先检查项目根目录
    project_root = Path(__file__).parent.parent
    executor_path = project_root / "executor.fsm"
    if executor_path.exists():
        return str(executor_path)

    # 检查当前目录
    current_dir = Path.cwd()
    executor_path = current_dir / "executor.fsm"
    if executor_path.exists():
        return str(executor_path)

    return None


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
        self._executor_loaded = False
        self._receive_thread = None
        self._receive_result = None
        self._receive_event = threading.Event()

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

    def new_model(self) -> dict:
        """
        创建空白模型（US-003 实现）。

        调用 controller.open("") 创建全新的空模型，并返回模型状态信息。
        如果 executor.fsm 已加载，会重新加载以维持执行通道。

        Returns:
            dict: 包含 'ok'、'message' 和 'object_count' 的字典
        """
        # 保存 executor 是否已加载的状态
        executor_was_loaded = self._executor_loaded

        # 创建新空模型 - 使用 open("") 创建空白模型
        self.controller.open("")

        # 重置执行器加载状态，重新加载以维持通道
        self._executor_loaded = False
        if executor_was_loaded:
            self.load_executor()

        # 获取当前模型对象数量
        try:
            script = "return numtostring(model().subnodes.length);"
            result = safe_evaluate(self.controller, script, allow_none=True)
            object_count = int(result.raw) if result.raw else 0
        except (ValueError, Exception):
            object_count = 0

        return {
            "ok": True,
            "message": f"新模型已创建，当前模型对象数量: {object_count}",
            "object_count": object_count
        }

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
        """执行 FlexSim 的 evaluate 通道。

        Phase 2 起，统一通过 safe_evaluate 做错误处理，避免直接抛出
        难以理解的底层异常。
        """
        if self.controller is None:
            raise ModelBuildError("尚未连接 FlexSim：请先调用 flexsim_launch 或 flexsim_connect。")

        # Phase 1 兼容：很多脚本在当前 FlexSimPy 环境下会返回 None。
        # 这里保持“尽量不抛错”的行为，将 None 视为 ""，避免中断旧工具（如 get_model_tree）。
        result = safe_evaluate(self.controller, expression, allow_none=True)
        return result.raw

    # === 消息传递 ===

    def send(self, message: str) -> str:
        """发送消息到 FlexSim"""
        self.controller.send(message)
        return f"消息已发送: {message}"

    def receive(self) -> str:
        """接收来自 FlexSim 的消息"""
        return self.controller.receive() or ""

    # === FlexScript 执行器 (US-001) ===

    def load_executor(self) -> str:
        """加载 executor.fsm 执行器模型"""
        if self._executor_loaded:
            return "执行器已加载"

        executor_path = _find_executor_model()
        if executor_path is None:
            raise FlexSimError(
                "executor.fsm 未找到。请先运行 create_executor_model.py 创建执行器模型。"
            )

        self.controller.open(executor_path)
        self._executor_loaded = True
        return f"执行器已加载: {executor_path}"

    def _receive_with_timeout(self, timeout: float = 5.0) -> str:
        """
        在后台线程中接收消息，支持超时

        Args:
            timeout: 超时时间（秒）

        Returns:
            接收到的消息内容
        """
        self._receive_result = None
        self._receive_event.clear()

        def receive_worker():
            try:
                self._receive_result = self.controller.receive()
            except Exception as e:
                self._receive_result = f"ERROR: {e}"
            finally:
                self._receive_event.set()

        # 启动接收线程
        self._receive_thread = threading.Thread(target=receive_worker)
        self._receive_thread.daemon = True
        self._receive_thread.start()

        # 等待结果或超时
        if self._receive_event.wait(timeout=timeout):
            result = self._receive_result
            if result is None:
                return ""
            # 检查是否有错误
            if isinstance(result, str) and result.startswith("ERROR:"):
                raise FlexSimError(result[6:].strip())
            return str(result)
        else:
            # 超时
            raise FlexSimError(f"接收 FlexScript 执行结果超时（{timeout}秒）")

    def execute_script(self, script: str, timeout: float = 5.0) -> str:
        """
        通过 send/receive 机制执行 FlexScript 代码。

        这是 US-001 的核心实现。流程：
        1. 确保 executor.fsm 已加载
        2. 通过 send() 发送 FlexScript 代码到执行器
        3. 通过 receive() 等待并获取执行结果

        Args:
            script: 要执行的 FlexScript 代码
            timeout: 接收结果的超时时间（秒）

        Returns:
            执行结果字符串

        Raises:
            FlexSimError: 执行失败或超时时抛出
        """
        if self.controller is None:
            raise FlexSimError("尚未连接 FlexSim：请先调用 flexsim_launch 或 flexsim_connect。")

        # 确保执行器模型已加载
        if not self._executor_loaded:
            self.load_executor()

        # 发送 FlexScript 代码
        self.controller.send(script)

        # 接收执行结果（带超时）
        result = self._receive_with_timeout(timeout)

        return result


# 单例全局客户端
_client = None

# 执行器模型路径
EXECUTOR_MODEL_PATH = str(Path(__file__).parent.parent / "executor.fsm")


def get_client() -> FlexSimClient:
    """获取全局 FlexSim 客户端实例"""
    global _client
    if _client is None:
        _client = FlexSimClient()
    return _client
