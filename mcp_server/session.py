"""FlexSim 会话管理 - 确保同时只有一个操作访问 FlexSim 引擎"""

import threading
from typing import Callable, Any


class FlexSimSession:
    """单例模式，确保同时只有一个操作访问 FlexSim 引擎"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._operation_lock = threading.Lock()
        self._initialized = True

    def execute(self, operation: Callable[[Any], Any], *args, **kwargs) -> Any:
        """
        串行化所有对 FlexSim 的操作。

        Args:
            operation: 要执行的操作函数
            *args: 操作函数的参数
            **kwargs: 操作函数的关键字参数

        Returns:
            操作函数的返回值
        """
        with self._operation_lock:
            return operation(*args, **kwargs)

    def execute_with_client(self, client_func: Callable, *args, **kwargs) -> Any:
        """
        使用全局客户端执行操作的便捷方法。

        Args:
            client_func: 接受 FlexSimClient 作为第一个参数的函数
            *args: 额外参数
            **kwargs: 关键字参数
        """
        from .flexsim_client import get_client
        client = get_client()
        return self.execute(client_func, client, *args, **kwargs)


# 全局会话实例
_session = None


def get_session() -> FlexSimSession:
    """获取全局会话实例"""
    global _session
    if _session is None:
        _session = FlexSimSession()
    return _session
