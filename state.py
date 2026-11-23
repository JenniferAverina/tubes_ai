
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
    knowledge_result: str
    rewritten_query: str
    search_attempt: int

    # Code Fixer Worker (Member 2)
    fixed_code: str
    fix_attempts: int

    # Human-in-the-Loop
    approval: Optional[bool]
    patch_applied: bool
    patch_result: str

    # Supervisor (Member 3)
    next_worker: str
    workflow_status: str

    # Workflow information
    messages: list[str]

    # validation
    validation_status: str
    validation_result: Optional[dict[str, Any]]
    validation_message: str

    react_trace: list[dict[str, Any]]