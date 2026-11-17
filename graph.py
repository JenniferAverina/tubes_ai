
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from agents.supervisor import (
    supervisor_node,
    supervisor_router
)
from agents.syntax_checker import syntax_checker_node
from agents.rag_specialist import rag_specialist_node
from agents.code_fixer import code_fixer_node


# ==========================================
# 1. APPLY PATCH
# ==========================================

def apply_patch_node(state: AgentState) -> dict:

    print("\n========== APPLY PATCH ==========")

    if state.get("approval") is not True:
        return {
            "patch_applied": False,
            "patch_result": "Patch rejected or not approved."
        }

    fixed_code = state.get("fixed_code")
    file_path = state.get("file_path")

    if not fixed_code or not file_path:
        return {
            "patch_applied": False,
            "patch_result": "Missing fixed code or file path."
        }

    workspace = Path("workspace").resolve()
    target = Path(file_path).resolve()

    # Pastikan target berada di dalam workspace
    if not target.is_relative_to(workspace):
        return {
            "patch_applied": False,
            "patch_result": "Target file must be inside workspace."
        }

    if not target.is_file():
        return {
            "patch_applied": False,
            "patch_result": "Target file does not exist."
        }

    target.write_text(fixed_code, encoding="utf-8")

    print(f"Patch applied: {target}")

    return {
        "patch_applied": True,
        "patch_result": f"Patch successfully applied to {target}"
    }


# ==========================================
# 2. CONDITIONAL ROUTING
# ==========================================

MAX_RAG_ATTEMPTS = 2


def route_after_rag(state: AgentState) -> str:

    knowledge_result = state.get("knowledge_result", "NOT_FOUND")
    search_attempt = state.get("search_attempt", 0)

    print("\n========== RAG ROUTER ==========")
    print("Knowledge result:", knowledge_result)
    print("Search attempt:", search_attempt)

    if knowledge_result != "NOT_FOUND":
        print("Next worker: code_fixer")
        return "code_fixer"

    if search_attempt < MAX_RAG_ATTEMPTS:
        print("Next worker: rag_specialist (retry)")
        return "rag_specialist"

    print("Next worker: code_fixer (fallback)")
    return "code_fixer"

def route_after_fixer(state: AgentState) -> str:

    if state.get("fixed_code"):
        return "apply_patch"

    return END


# ==========================================
# 3. BUILD LANGGRAPH
# ==========================================

builder = StateGraph(AgentState)

builder.add_node("syntax_checker", syntax_checker_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("rag_specialist", rag_specialist_node)
builder.add_node("code_fixer", code_fixer_node)
builder.add_node("apply_patch", apply_patch_node)


# ==========================================
# 4. DEFINE EDGES
# ==========================================

builder.add_edge(START, "syntax_checker")

builder.add_edge("syntax_checker", "supervisor")

builder.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "rag_specialist": "rag_specialist",
        "END": END
    }
)

builder.add_conditional_edges(
    "rag_specialist",
    route_after_rag,
    {
        "rag_specialist": "rag_specialist",
        "code_fixer": "code_fixer"
    }
)

builder.add_conditional_edges(
    "code_fixer",
    route_after_fixer,
    {
        "apply_patch": "apply_patch",
        END: END
    }
)

builder.add_edge("apply_patch", END)


# ==========================================
# 5. CHECKPOINTER + HITL
# ==========================================


memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["apply_patch"]
)

