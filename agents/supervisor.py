
from state import AgentState
from tools.trace_logger import log_trace


# ==========================================
# 1. CONFIGURATION
# ==========================================

MAX_RAG_ATTEMPTS = 2


# ==========================================
# 2. SUPERVISOR NODE
# ==========================================

def supervisor_node(state: AgentState) -> dict:

    print("\n========== SUPERVISOR ==========")

    diagnosis = state.get("diagnosis") or {}

    status = diagnosis.get("status")

    search_attempt = state.get("search_attempt", 0)

    knowledge_result = state.get("knowledge_result")

    fixed_code = state.get("fixed_code")

    # Preserve previous trace
    trace = list(state.get("react_trace", []))

    messages = list(state.get("messages", []))

    # ======================================
    # 3. DETERMINE NEXT WORKER
    # ======================================

    if not diagnosis:

        next_worker = "END"
        workflow_status = "DIAGNOSTIC_FAILED"

        thought = (
            "Diagnosis is unavailable. "
            "The workflow cannot continue safely."
        )

    elif status == "SUCCESS":

        next_worker = "END"
        workflow_status = "COMPLETED"

        thought = (
            "The diagnostic agent found no code errors. "
            "The debugging workflow can finish."
        )

    elif status == "ERROR":

        # If Code Fixer already generated code,
        # send it to validation.
        if fixed_code:

            next_worker = "validation"
            workflow_status = "FIX_GENERATED"

            thought = (
                "A code repair has been generated. "
                "The next step is to validate the repaired code."
            )

        # If Knowledge Base contains useful information,
        # send it to Code Fixer.
        elif knowledge_result and knowledge_result != "NOT_FOUND":

            next_worker = "code_fixer"
            workflow_status = "KNOWLEDGE_FOUND"

            thought = (
                "Knowledge Base information was retrieved. "
                "Code Fixer can use it to generate a repair."
            )

        # If knowledge is unavailable, retry RAG
        # while attempts remain.
        elif search_attempt < MAX_RAG_ATTEMPTS:

            next_worker = "rag_specialist"
            workflow_status = "SEARCHING_KNOWLEDGE"

            thought = (
                "Knowledge Base information is unavailable. "
                "Another retrieval attempt is required, "
                "allowing the RAG agent to rewrite its query."
            )

        # If maximum attempts are reached,
        # use Code Fixer fallback.
        else:

            next_worker = "code_fixer"
            workflow_status = "USING_FALLBACK"

            thought = (
                "Maximum RAG attempts reached. "
                "Code Fixer will use standard debugging "
                "best practices as fallback."
            )

    else:

        next_worker = "END"
        workflow_status = "DIAGNOSTIC_FAILED"

        thought = (
            f"Unexpected diagnosis status: {status}. "
            "The workflow will terminate."
        )

    # ======================================
    # 4. LOG ROUTING DECISION
    # ======================================

    print("Diagnosis status:", status)
    print("Search attempt:", search_attempt)
    print("Knowledge result:", knowledge_result)
    print("Next worker:", next_worker)

    messages.append(
        f"Supervisor selected: {next_worker}"
    )

    trace_entry = log_trace(
        agent="SUPERVISOR",

        thought=thought,

        action=f"Route workflow to {next_worker}.",

        observation=(
            f"Diagnosis: {status}, "
            f"RAG attempts: {search_attempt}/{MAX_RAG_ATTEMPTS}, "
            f"Workflow status: {workflow_status}."
        )
    )

    trace.append(trace_entry)

    # ======================================
    # 5. RETURN UPDATED STATE
    # ======================================

    return {
        "next_worker": next_worker,
        "workflow_status": workflow_status,
        "messages": messages,
        "react_trace": trace
    }


# ==========================================
# 6. SUPERVISOR ROUTER
# ==========================================

def supervisor_router(state: AgentState) -> str:

    next_worker = state.get("next_worker", "END")

    print("\n========== SUPERVISOR ROUTER ==========")
    print("Routing decision:", next_worker)

    return next_worker
