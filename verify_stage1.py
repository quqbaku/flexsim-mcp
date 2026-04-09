"""Stage 1 本地一键验收（代码侧）"""

from __future__ import annotations

import os
import sys
import traceback

# 设置 PATH（必须在导入 FlexSimPy 之前）
flexsim_dir = r"C:\Program Files\FlexSim 2026\program"
os.environ["PATH"] = flexsim_dir + os.pathsep + os.environ.get("PATH", "")
sys.path.insert(0, r"C:\Program Files\FlexSim 2026")

from mcp_server.flexsim_client import get_client


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    client = get_client()

    try:
        launch_msg = client.launch()
        checks.append(("launch", True, launch_msg))

        # 空路径不应阻塞，也不应触发文件选择页
        open_msg = client.open_model("")
        checks.append(("open_model_empty_path", True, open_msg))

        # 当前 SDK evaluate 的可用口径：节点路径求值
        model_time = client.evaluate("MAIN:/project/exec/time")
        ok_time = model_time is not None and str(model_time) != ""
        checks.append(("evaluate_model_time_path", ok_time, f"value={model_time!r}"))

        # 当前 SDK 下脚本字符串不是 evaluate 的有效输入，应抛明确错误
        try:
            client.evaluate("return time();")
            checks.append(("evaluate_script_rejected", False, "expected error, got success"))
        except Exception as exc:
            checks.append(("evaluate_script_rejected", True, str(exc)))

        client.stop()
    except Exception as exc:
        checks.append(("unexpected_exception", False, f"{type(exc).__name__}: {exc}"))
        traceback.print_exc()
        try:
            client.stop()
        except Exception:
            pass

    print("=== Stage 1 Code-side Verification ===")
    all_pass = True
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"[{status}] {name}: {detail}")

    print()
    print("Result:", "PASS" if all_pass else "FAIL")
    if all_pass:
        print("Note: Code-side Stage 1 passed; Claude Desktop integration recommended for final verification.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
