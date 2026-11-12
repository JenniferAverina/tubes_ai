
from state import AgentState


def supervisor_node(state: AgentState) -> dict:

    print("\n========== SUPERVISOR ==========")

    diagnosis = state.get("diagnosis")

    # Jika diagnosis tidak tersedia
    if not diagnosis:

        return {
            "next_worker": "END",
            "workflow_status": "DIAGNOSTIC_FAILED",
            "messages": ["Supervisor: Diagnosis tidak tersedia."]
        }

    status = diagnosis.get("status")

    print("Diagnosis status:", status)

    # Jika kode tidak memiliki error
    if status == "SUCCESS":

        next_worker = "END"
        workflow_status = "COMPLETED"

    # Jika ditemukan error
    elif status == "ERROR":

        next_worker = "rag_specialist"
        workflow_status = "DIAGNOSIS_COMPLETED"

    else:

        next_worker = "END"
        workflow_status = "DIAGNOSTIC_FAILED"

    print("Next worker:", next_worker)

    return {
        "next_worker": next_worker,
        "workflow_status": workflow_status,
        "messages": [
            f"Supervisor selected: {next_worker}"
        ]
    }


def supervisor_router(state: AgentState) -> str:

    return state.get("next_worker", "END")
