
from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):

    # Input
    source_code: str
    file_path: str

    # Syntax Checker Worker (Member 1)
    syntax_result: Optional[dict[str, Any]]
    execution_result: Optional[dict[str, Any]]
    diagnosis: Optional[dict[str, Any]]
    react_trace: list[dict[str, Any]]

    # RAG Specialist Worker (Member 2)
    rag_query: str
    rag_result: list[dict[str, Any]]
    rag_status: str
    rewritten_query: str
    retry_count: int

    # Code Fixer Worker (Member 2)
    fixed_code: str
    fix_explanation: str

    # Human-in-the-Loop
    approval: Optional[bool]
    patch_applied: bool
    patch_result: str

    # Supervisor (Member 3)
    next_worker: str
    workflow_status: str

    # Workflow information
    messages: list[str]
