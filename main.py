
from pathlib import Path
from uuid import uuid4


from graph import graph
from tools.trace_logger import display_trace
from test_case import TEST_CASES
# ==========================================
# 1. HARDCODED SOURCE CODE
# ==========================================

# SOURCE_CODE = """
# x = 10
# y = 0
# print(x / y)
# """
SOURCE_CODE = TEST_CASES["zerodivision"]

DEBUG_MODE = True


# ==========================================
# 2. RUN AUTOMATED DEBUGGER
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
        "approval": None,
    }

    print("\n========== AUTOMATED CODE DEBUGGER ==========")

    # ==========================================
    # 3. START GRAPH
    # ==========================================

    result = graph.invoke(initial_state, config=config)

    # ==========================================
    # 4. CHECK HITL INTERRUPT
    # ==========================================

    snapshot = graph.get_state(config)

    if "apply_patch" in snapshot.next:

        print("\n========== HUMAN-IN-THE-LOOP ==========")

        print("\nOriginal Code:")
        print(target_file.read_text(encoding="utf-8"))

        print("\n========== PROPOSED FIX ==========")
        print(result.get("fixed_code", ""))

        print("\nValidation:", result.get("validation_status"))

        approval_input = input(
            "\nApply this patch? (y/n): "
        ).strip().lower()

        approval = approval_input == "y"

        # Update approval in checkpoint state
        graph.update_state(
            config,
            {"approval": approval}
        )

        # Resume graph from interrupted apply_patch node
        result = graph.invoke(None, config=config)

    # ==========================================
    # 5. DISPLAY RESULT
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
# 6. MAIN
# ==========================================

if __name__ == "__main__":

    print("\n==========================================")
    print("       AUTOMATED CODE DEBUGGER")
    print("==========================================")

    run_debugger(SOURCE_CODE)
