
from pathlib import Path
from graph import graph
from test_case import TEST_CASES

def run_debugger(source_code: str):

    # 1. Siapkan workspace dan file target
    workspace = Path("workspace").resolve()
    workspace.mkdir(exist_ok=True)

    target_file = workspace / "buggy_code.py"
    target_file.write_text(source_code, encoding="utf-8")

    # 2. Initial state
    initial_state = {
        "source_code": source_code,
        "file_path": str(target_file),
        "approval": None,
        "patch_applied": False,
        "react_trace": [],
        "messages": [],
        "search_attempt": 0,
        "fix_attempts": 0
    }

    config = {
        "configurable": {
            "thread_id": "debug-session-001"
        }
    }

    print("\n========== AUTOMATED DEBUGGER ==========")

    # 3. Jalankan graph
    result = graph.invoke(
        initial_state,
        config=config
    )

    # 4. Periksa graph state
    snapshot = graph.get_state(config)

    print("\n========== DEBUG GRAPH STATE ==========")
    print("Next nodes:", snapshot.next)
    print(
        "Fixed code exists:",
        bool(snapshot.values.get("fixed_code"))
    )

    # 5. Human-in-the-Loop
    if snapshot.next and "apply_patch" in snapshot.next:

        print("\n========== HUMAN APPROVAL ==========")
        print("\nProposed Fixed Code:")
        print(snapshot.values.get("fixed_code", ""))

        choice = input(
            "\nApply this patch? (y/n): "
        ).strip().lower()

        approval = choice == "y"

        graph.update_state(
            config,
            {"approval": approval}
        )

        # Resume graph setelah keputusan user
        result = graph.invoke(
            None,
            config=config
        )

    else:
        result = snapshot.values

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


if __name__ == "__main__":

    code = """
x = 10
y = 0
print(x / y)
"""

    run_debugger(TEST_CASES[""])
