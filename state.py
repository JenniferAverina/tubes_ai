
from typing import TypedDict, Optional, Any


class AgentState(TypedDict, total=False):

    # USER INPUT
    source_code: str
    file_path: str

    # MEMBER 1: SYNTAX CHECKER
    syntax_result: Optional[dict[str, Any]]
    execution_result: Optional[dict[str, Any]]
    diagnosis: Optional[dict[str, Any]]
    react_trace: list[dict[str, Any]]

    # MEMBER 2: RAG SPECIALIST
    rag_query: str
    rag_result: list[dict[str, Any]]
    rag_status: str
    rewritten_query: str
    retry_count: int

    # MEMBER 2: CODE FIXER
    fixed_code: str
    fix_explanation: str

    # HUMAN-IN-THE-LOOP
    approval: Optional[bool]

    # APPLY PATCH
    patch_applied: bool
    patch_result: str

    # SUPERVISOR
    next_worker: str
    workflow_status: str

    # LOGGING
    messages: list[str]
