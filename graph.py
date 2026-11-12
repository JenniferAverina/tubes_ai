
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from agents.supervisor import (
    supervisor_node,
    supervisor_router
)

from agents.syntax_checker import syntax_checker_node


# ==========================================
# 1. RAG SPECIALIST PLACEHOLDER
# ==========================================

def rag_specialist_node(state: AgentState) -> dict:

    print("\n========== RAG SPECIALIST ==========")

    # Menunggu implementasi Anggota 2

    return {
        "rag_status": "PENDING_MEMBER_2",
        "workflow_status": "WAITING_FOR_RAG",
        "messages": [
            "RAG Specialist belum diimplementasikan."
        ]
    }


# ==========================================
# 2. CODE FIXER PLACEHOLDER
# ==========================================

def code_fixer_node(state: AgentState) -> dict:

    print("\n========== CODE FIXER ==========")

    # Menunggu implementasi Anggota 2

    return {
        "workflow_status": "WAITING_FOR_CODE_FIXER",
        "messages": [
            "Code Fixer belum diimplementasikan."
        ]
    }


# ==========================================
# 3. APPROVAL CHECK
# ==========================================

def approval_node(state: AgentState) -> dict:

    print("\n========== HUMAN APPROVAL ==========")

    if state.get("approval") is True:

        return {
            "messages": ["Human approved the code patch."]
        }

    return {
        "messages": ["Patch approval was not granted."]
    }


# ==========================================
# 4. APPLY PATCH
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

    target = Path(file_path).resolve()

    # Batasi patch hanya ke folder workspace
    workspace = Path("workspace").resolve()

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

    return {
        "patch_applied": True,
        "patch_result": f"Patch successfully applied to {target}"
    }


# ==========================================
# 5. CONDITIONAL ROUTING
# ==========================================

def route_after_rag(state: AgentState) -> str:

    if state.get("rag_status") == "FOUND":

        return "code_fixer"

    # Jika belum ditemukan atau RAG belum tersedia
    return END


def route_after_fixer(state: AgentState) -> str:

    if state.get("fixed_code"):

        return "approval"

    return END


# ==========================================
# 6. BUILD LANGGRAPH
# ==========================================

builder = StateGraph(AgentState)

builder.add_node(
    "syntax_checker",
    syntax_checker_node
)

builder.add_node(
    "supervisor",
    supervisor_node
)

builder.add_node(
    "rag_specialist",
    rag_specialist_node
)

builder.add_node(
    "code_fixer",
    code_fixer_node
)

builder.add_node(
    "approval",
    approval_node
)

builder.add_node(
    "apply_patch",
    apply_patch_node
)


# ==========================================
# 7. DEFINE EDGES
# ==========================================

builder.add_edge(START, "syntax_checker")

builder.add_edge(
    "syntax_checker",
    "supervisor"
)

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
        "code_fixer": "code_fixer",
        END: END
    }
)

builder.add_conditional_edges(
    "code_fixer",
    route_after_fixer,
    {
        "approval": "approval",
        END: END
    }
)

builder.add_edge("approval", "apply_patch")


# ==========================================
# 8. CHECKPOINTER + HITL
# ==========================================

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["apply_patch"]
)
