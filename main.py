
from pathlib import Path
from uuid import uuid4
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

from graph import graph
from tools.trace_logger import display_trace


# ==========================================
# 1. HARDCODED SOURCE CODE
# ==========================================

SOURCE_CODE = """
x = 10
y = 0

print(x / y)
"""


# ==========================================
# 2. CONFIGURATION
# ==========================================

DEBUG_MODE = False


# ==========================================
# 3. RUN AUTOMATED DEBUGGER
# ==========================================

def run_debugger(source_code: str):

    workspace = Path("workspace").resolve()
    workspace.mkdir(exist_ok=True)

    target_file = workspace / "buggy_code.py"
    target_file.write_text(source_code, encoding="utf-8")

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    initial_state = {
        "source_code": source_code,
        "file_path": str(target_file),
    }

    print("\n========== AUTOMATED CODE DEBUGGER ==========")

    if DEBUG_MODE:
        result = graph.invoke(initial_state, config=config)
    else:
        captured_output = StringIO()

        with redirect_stdout(captured_output), redirect_stderr(captured_output):
            result = graph.invoke(initial_state, config=config)

    # ==========================================
    # 4. DISPLAY RESULT
    # ==========================================

    print("\n========== DEBUGGER RESULT ==========")

    print(f"Target File : {target_file}")
    print(f"Workflow    : {result.get('workflow_status', 'Completed')}")

    if result.get("diagnosis"):
        print(f"Diagnosis   : {result['diagnosis']}")

    if result.get("knowledge_result"):
        print(f"Knowledge   : {result['knowledge_result']}")

    if result.get("fixed_code"):
        print("\n========== PROPOSED FIX ==========")
        print(result["fixed_code"])

    if result.get("patch_applied"):
        print("\nPatch Status: APPLIED")
    elif result.get("approval") is False:
        print("\nPatch Status: REJECTED")
    else:
        print("\nPatch Status: NOT APPLIED")

    if DEBUG_MODE and result.get("react_trace"):
        display_trace(result["react_trace"])


# ==========================================
# 5. MAIN
# ==========================================

if __name__ == "__main__":

    print("\n==========================================")
    print("       AUTOMATED CODE DEBUGGER")
    print("==========================================")

    run_debugger(SOURCE_CODE)
