#!/usr/bin/env python3
"""
创建 executor.fsm 执行器模型的脚本

此脚本在 FlexSim 环境中运行，创建 executor.fsm 模型。
executor.fsm 是一个预置模型，内含 OnMessage 触发器，
接收 FlexScript 字符串、执行并回传结果。

用法:
    python create_executor_model.py

注意: 需要在配置好 FlexSimPy 的环境中运行。
"""

import os
import sys
from pathlib import Path

# 添加 FlexSim 路径
def setup_flexsim_path():
    """从 config.toml 读取 FlexSim 路径并配置"""
    config_path = Path(__file__).parent / "config.toml"
    if config_path.exists():
        import tomllib
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        program_dir = config.get("flexsim", {}).get("program_dir")
        if program_dir:
            if program_dir not in sys.path:
                sys.path.insert(0, program_dir)
            flexsim_bin = Path(program_dir) / "program"
            if str(flexsim_bin) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(flexsim_bin) + os.pathsep + os.environ.get("PATH", "")

setup_flexsim_path()

import FlexSimPy as fp


def create_executor_model():
    """
    创建 executor.fsm 执行器模型

    该模型的核心逻辑:
    1. OnMessage 触发器接收 FlexScript 字符串
    2. 使用 evaluate() 执行收到的 FlexScript
    3. 将结果通过 send() 回传给 Python 端

    工作原理:
    - Python 端调用 controller.send(flexscript_code) 发送 FlexScript 代码
    - FlexSim 模型的 OnMessage 触发器接收消息
    - 触发器使用 evaluate() 执行代码
    - 触发器调用 send() 将结果发回
    - Python 端调用 controller.receive() 获取结果
    """
    print("启动 FlexSim...")
    controller = fp.launch(
        evaluationLicense=True,
        showGUI=False,
        programDir=r"C:\Program Files\FlexSim 2026\program"
    )

    print("创建执行器模型...")

    # 使用 FlexScript 创建执行器对象
    # 我们创建一个带有 OnMessage 触发器的对象

    executor_script = r"""
    // 创建执行器对象
    Object executor = createinstance(library().find("BasicFR"), model());
    executor.name = "FlexScriptExecutor";

    // 设置执行器位置（移到视窗之外，避免干扰）
    executor.setLocation(1000, 1000, 0);

    // 返回创建成功信息
    return "Executor created: " + executor.name;
    """

    result = controller.evaluate(executor_script)
    print(f"创建结果: {result}")

    # 添加 OnMessage 触发器到执行器对象
    # OnMessage 触发器的 eventType 是 2001
    add_trigger_script = r"""
    Object executor = model().find("FlexScriptExecutor");
    if (executor) {
        // 获取触发器容器
        treenode triggers = executor.find("eventtriggers");
        if (!triggers) {
            // 如果不存在触发器容器，创建一个
            triggers = createinstance(library().find("Tools"), executor);
            triggers.name = "eventtriggers";
        }

        // 创建 OnMessage 触发器
        treenode onMsg = createinstance(library().find("MsgTrigger"), triggers);
        onMsg.name = "OnMessage";
        onMsg.eventType = 2001;  // MSG_TRIGGER type for OnMessage

        return "Trigger created successfully";
    }
    return "Executor not found";
    """

    result = controller.evaluate(add_trigger_script)
    print(f"添加触发器结果: {result}")

    # 设置 OnMessage 触发器的代码
    # 这是核心逻辑：当收到消息时，执行 FlexScript 并返回结果
    trigger_code = r"""
    // OnMessage 触发器代码
    // parstr(1) 包含发送的消息内容（FlexScript 代码）

    string flexscriptCode = parstr(1);

    // 执行 FlexScript 并获取结果
    Variant result = evaluate(flexscriptCode);

    // 将结果发送回调用者
    // sendToController(result) 将结果发送回 Python 端
    sendtomain(result);

    return 1;
    """

    # 设置触发器代码 - 需要处理多行字符串
    trigger_code_escaped = trigger_code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

    set_trigger_script = f'''
    Object executor = model().find("FlexScriptExecutor");
    if (executor) {{
        treenode onMsg = executor.find("eventtriggers/OnMessage");
        if (onMsg) {{
            onMsg.script = "{trigger_code_escaped}";
            return "Trigger code set successfully";
        }}
        return "OnMessage trigger not found";
    }}
    return "Executor not found";
    '''

    result = controller.evaluate(set_trigger_script)
    print(f"设置触发器代码结果: {result}")

    # 保存模型
    output_path = Path(__file__).parent / "executor.fsm"
    output_path_str = str(output_path).replace('\\', '\\\\')

    save_script = f'''
    saveModel("{output_path_str}");
    return "Model saved to {output_path_str}";
    '''

    result = controller.evaluate(save_script)
    print(f"保存结果: {result}")

    # 验证保存的文件
    if output_path.exists():
        print(f"executor.fsm 已创建: {output_path.absolute()}")
        print(f"文件大小: {output_path.stat().st_size} bytes")
    else:
        print(f"警告: executor.fsm 文件未找到")

    controller.stop()
    print("完成")


if __name__ == "__main__":
    create_executor_model()