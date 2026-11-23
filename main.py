
from pathlib import Path
from uuid import uuid4

from graph import graph

from tools.trace_logger import display_trace
# ==========================================
# 1. RUN AUTOMATED DEBUGGER
# ==========================================

def run_debugger(source_code: str):

    # Prepare workspace
    workspace = Path("workspace").resolve()
    workspace.mkdir(exist_ok=True)

    target_file = workspace / "buggy_code.py"

    target_file.write_text(
        source_code,
        encoding="utf-8"
    )

    # ======================================
    # 2. INITIAL STATE
    # ======================================

    initial_state = {
        "source_code": source_code,
        "file_path": str(target_file),

        "approval": None,
        "patch_applied": False,

        "react_trace": [],
        "messages": [],

        "search_attempt": 0,
        "fix_attempts": 0,

        "knowledge_result": "NOT_FOUND"
    }

    # Unique session ID for every run
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    print("\n========== AUTOMATED DEBUGGER ==========")

    # ======================================
    # 3. RUN GRAPH
    # ======================================

    result = graph.invoke(
        initial_state,
        config=config
    )

    # ======================================
    # 4. CHECK GRAPH STATE
    # ======================================

    snapshot = graph.get_state(config)

    print("\n========== DEBUG GRAPH STATE ==========")

    print("Next nodes:", snapshot.next)

    print(
        "Fixed code exists:",
        bool(snapshot.values.get("fixed_code"))
    )

    # ======================================
    # 5. HUMAN-IN-THE-LOOP
    # ======================================

    if "apply_patch" in snapshot.next:

        print("\n========== HUMAN APPROVAL ==========")

        print("\nProposed Fixed Code:")
        print(snapshot.values.get("fixed_code", ""))

        choice = input(
            "\nApply this patch? (y/n): "
        ).strip().lower()

        approval = choice == "y"

        print(
            "\nApproval decision:",
            "APPROVED" if approval else "REJECTED"
        )

        # Update approval state
        graph.update_state(
            config,
            {"approval": approval}
        )

        # Resume graph after human decision
        result = graph.invoke(
            None,
            config=config
        )

    # ======================================
    # 6. GET FINAL STATE
    # ======================================

    display_trace(result.get("react_trace", []))

    # ======================================
    # 7. DISPLAY FINAL RESULT
    # ======================================

    print("\n========== DEBUGGER RESULT ==========")

    print("\nDiagnosis:")
    print(result.get("diagnosis"))

    print("\nKnowledge Result:")
    print(result.get("knowledge_result"))

    print("\nFixed Code:")
    print(result.get("fixed_code"))

    print("\nPatch Applied:")
    print(result.get("patch_applied"))

    print("\nPatch Result:")
    print(result.get("patch_result"))

    print("\nWorkflow Status:")
    print(result.get("workflow_status"))

    print("\nSupervisor Decision:")
    print(result.get("next_worker"))

    print("\nMessages:")

    for message in result.get("messages", []):
        print("-", message)

   
    
    print("\n=======================================")


# ==========================================
# 9. MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    code = """
    x = 10
    y = 0
    print(x / y)
    """


    source_code = """
    x = 10
    y = 0

    print(x / y)
    """

    run_debugger(source_code)
