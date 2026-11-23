
from pathlib import Path
from uuid import uuid4
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

from graph import graph
from test_case import TEST_CASES
from tools.trace_logger import display_trace


# ==========================================
# CONFIGURATION
# ==========================================

DEBUG_MODE = False


# ==========================================
# GRAPH EXECUTION
# ==========================================

def invoke_graph(input_state, config):

    if DEBUG_MODE:
        return graph.invoke(input_state, config=config)

    # Hide internal logs in Demo Mode
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        return graph.invoke(input_state, config=config)


# ==========================================
# HELPER: GET VALIDATION STATUS
# ==========================================

def get_validation_status(react_trace):

    for entry in reversed(react_trace):
        if entry.get("agent") == "VALIDATION":
            observation = str(entry.get("observation", ""))

            if "VALID" in observation:
                return "PASSED"

            if "INVALID" in observation:
                return "FAILED"

    return None


# ==========================================
# HELPER: DISPLAY AGENT SUMMARY
# ==========================================

def display_agent_summary(result):

    trace = result.get("react_trace", [])
    diagnosis = result.get("diagnosis") or {}

    print("\n========== AGENT SUMMARY ==========")

    # Syntax Checker
    if any(entry.get("agent") == "SYNTAX_CHECKER" for entry in trace):
        error_type = diagnosis.get("error_type")

        if error_type:
            print(f"[1] Syntax Checker : {error_type} DETECTED")
        else:
            print("[1] Syntax Checker : NO ERROR DETECTED")

    # RAG Specialist
    if any(entry.get("agent") == "RAG_SPECIALIST" for entry in trace):
        knowledge = result.get("knowledge_result", "NOT_FOUND")

        if knowledge == "NOT_FOUND":
            print("[2] RAG Specialist : KNOWLEDGE NOT FOUND")
        else:
            print("[2] RAG Specialist : KNOWLEDGE FOUND")

    # Code Fixer
    if any(entry.get("agent") == "CODE_FIXER" for entry in trace):
        if result.get("fixed_code"):
            print("[3] Code Fixer     : FIX GENERATED")
        else:
            print("[3] Code Fixer     : NO FIX GENERATED")

    # Validation
    validation_status = get_validation_status(trace)

    if validation_status:
        print(f"[4] Validation     : {validation_status}")

    # Human Approval
    approval = result.get("approval")

    if approval is not None:
        status = "APPROVED" if approval else "REJECTED"
        print(f"[5] Human Approval : {status}")

    # Apply Patch
    if approval is True or approval is False:
        if result.get("patch_applied"):
            print("[6] Apply Patch    : SUCCESS")
        else:
            print("[6] Apply Patch    : REJECTED / NOT APPLIED")


# ==========================================
# RUN AUTOMATED DEBUGGER
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
    # INITIAL STATE
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

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    print("\n========== AUTOMATED DEBUGGER ==========")
    print("Mode:", "DEBUG" if DEBUG_MODE else "DEMO")

    # ======================================
    # RUN GRAPH
    # ======================================

    result = invoke_graph(initial_state, config)

    # ======================================
    # CHECK GRAPH STATE
    # ======================================

    snapshot = graph.get_state(config)

    if DEBUG_MODE:
        print("\n========== DEBUG GRAPH STATE ==========")
        print("Next nodes:", snapshot.next)
        print(
            "Fixed code exists:",
            bool(snapshot.values.get("fixed_code"))
        )

    # ======================================
    # HUMAN-IN-THE-LOOP
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

        graph.update_state(
            config,
            {"approval": approval}
        )

        # Resume graph after human decision
        result = invoke_graph(None, config)

    # ======================================
    # GET FINAL STATE
    # ======================================

    # Read the latest graph state
    final_snapshot = graph.get_state(config)
    result = final_snapshot.values

    # ======================================
    # DISPLAY DEBUG TRACE
    # ======================================

    if DEBUG_MODE:
        display_trace(result.get("react_trace", []))

    # ======================================
    # FINAL RESULT
    # ======================================

    print("\n========== DEBUGGER RESULT ==========")

    if DEBUG_MODE:

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

    else:

        display_agent_summary(result)

        diagnosis = result.get("diagnosis") or {}

        print("\n========== FINAL RESULT ==========")

        if isinstance(diagnosis, dict):
            print("Diagnosis:", diagnosis.get("error_type", diagnosis.get("status")))
        else:
            print("Diagnosis:", diagnosis)

        print("Knowledge Result:", result.get("knowledge_result"))

        print(
            "Fixed Code Generated:",
            bool(result.get("fixed_code"))
        )

        print("Patch Applied:", result.get("patch_applied"))
        print("Workflow Status:", result.get("workflow_status"))

    print("\n=======================================")


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    print("\n========== AVAILABLE TEST CASES ==========")

    for index, test_name in enumerate(TEST_CASES, start=1):
        print(f"{index}. {test_name}")

    choice = input("\nSelect test case: ").strip().lower()

    if choice not in TEST_CASES:
        print("Invalid test case!")
    else:
        print(f"\nRunning test case: {choice}")
        run_debugger(TEST_CASES[choice])
