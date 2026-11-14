
from graph import graph


def run_debugger(source_code: str):

    initial_state = {
        "source_code": source_code,
        "approval": None,
        "patch_applied": False,
        "react_trace": [],
        "messages": []
    }

    config = {
        "configurable": {
            "thread_id": "debug-session-001"
        }
    }

    print("\n========== AUTOMATED DEBUGGER ==========")

    result = graph.invoke(
        initial_state,
        config=config
    )

    print("\n========== DEBUGGER RESULT ==========")

    print("Diagnosis:")
    print(result.get("diagnosis"))

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
y = 2
print(x / y)
"""

    run_debugger(code)
