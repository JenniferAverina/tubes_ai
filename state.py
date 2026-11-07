
from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state untuk seluruh AI Debugger System.
    Digunakan oleh Supervisor dan semua Worker Nodes.
    """

    # Input dari user
    source_code: str

    # Anggota 1 - Code Diagnostic
    syntax_result: dict[str, Any] | None
    execution_result: dict[str, Any] | None
    diagnosis: dict[str, Any] | None

    # Anggota 2 - RAG Specialist
    knowledge_result: Any
    rewritten_query: str
    search_attempt: int

    # Anggota 2 - Code Fixer
    fixed_code: str
    fix_attempts: int

    # Anggota 3 - Supervisor & Human-in-the-Loop
    next_agent: str
    approval_status: str
    final_status: str

    # Informasi proses ReAct
    react_trace: list[dict[str, Any]]
