
import ast
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

from tools.trace_logger import log_trace

import subprocess
import sys
import tempfile

# ==========================================
# 1. VALIDATION NODE
# ==========================================


def validation_node(state: AgentState) -> dict:

    print("\n========== VALIDATION ==========")

    fixed_code = state.get("fixed_code", "")
    trace = list(state.get("react_trace", []))

    validation_status = "INVALID"
    validation_message = ""
    validation_result = {}

    if not fixed_code.strip():

        validation_message = "Fixed code is empty."

        validation_result = {
            "status": "ERROR",
            "error_type": "EmptyCode",
            "error_message": validation_message
        }

    else:
        try:
            # STEP 1: Syntax validation
            ast.parse(fixed_code)

            print("Syntax validation: PASSED")

            # STEP 2: Runtime validation
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                encoding="utf-8",
                delete=False
            ) as temp_file:

                temp_file.write(fixed_code)
                temp_path = temp_file.name

            try:
                execution = subprocess.run(
                    [sys.executable, temp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if execution.returncode == 0:

                    validation_status = "VALID"
                    validation_message = (
                        "Syntax and runtime validation passed."
                    )

                    validation_result = {
                        "status": "SUCCESS",
                        "stdout": execution.stdout,
                        "stderr": execution.stderr,
                        "returncode": execution.returncode
                    }

                else:

                    validation_message = (
                        "Runtime validation failed."
                    )

                    validation_result = {
                        "status": "ERROR",
                        "error_type": "RuntimeError",
                        "error_message": execution.stderr,
                        "returncode": execution.returncode
                    }

            finally:
                Path(temp_path).unlink(missing_ok=True)

        except SyntaxError as error:

            validation_message = (
                f"Generated code contains SyntaxError: {error}"
            )

            validation_result = {
                "status": "ERROR",
                "error_type": "SyntaxError",
                "error_message": str(error),
                "line": error.lineno
            }

        except subprocess.TimeoutExpired:

            validation_message = (
                "Runtime validation timed out after 10 seconds."
            )

            validation_result = {
                "status": "ERROR",
                "error_type": "TimeoutExpired",
                "error_message": validation_message
            }

        except OSError as error:

            validation_message = str(error)

            validation_result = {
                "status": "ERROR",
                "error_type": "OSError",
                "error_message": validation_message
            }

    print("Validation status:", validation_status)
    print("Validation message:", validation_message)

    trace_entry = log_trace(
        agent="VALIDATION",
        thought=(
            "Checking generated code through syntax "
            "and runtime validation."
        ),
        action=(
            "Execute ast.parse() and run the generated "
            "Python code in a temporary file."
        ),
        observation=(
            f"Validation status: {validation_status}. "
            f"{validation_message}"
        )
    )

    trace.append(trace_entry)

    return {
        "validation_status": validation_status,
        "validation_message": validation_message,
        "validation_result": validation_result,
        "workflow_status": (
            "VALIDATION_PASSED"
            if validation_status == "VALID"
            else "VALIDATION_FAILED"
        ),
        "react_trace": trace
    }



# ==========================================
# 2. APPLY PATCH NODE
# ==========================================

def apply_patch_node(state: AgentState) -> dict:

    print("\n========== APPLY PATCH ==========")

    trace = list(state.get("react_trace", []))

    def finish_patch(
        success: bool,
        result: str,
        thought: str,
        action: str
    ) -> dict:

        trace_entry = log_trace(
            agent="APPLY_PATCH",
            thought=thought,
            action=action,
            observation=result
        )

        trace.append(trace_entry)

        return {
        "patch_applied": success,
        "patch_result": result,
        "workflow_status": (
            "PATCH_APPLIED"
            if success
            else (
                "PATCH_REJECTED"
                if state.get("approval") is False
                else "PATCH_FAILED"
            )
        ),
        "react_trace": trace
    }

    # ======================================
    # CHECK APPROVAL
    # ======================================

    if state.get("approval") is not True:

        return finish_patch(
            success=False,
            result="Patch rejected or not approved.",

            thought=(
                "Patch approval was not granted. "
                "The original source file must remain unchanged."
            ),

            action="Reject patch application."
        )

    # ======================================
    # READ PATCH DATA
    # ======================================

    fixed_code = state.get("fixed_code")
    file_path = state.get("file_path")

    if not fixed_code or not file_path:

        return finish_patch(
            success=False,
            result="Missing fixed code or file path.",

            thought=(
                "Required patch information is missing. "
                "The patch cannot be applied safely."
            ),

            action="Stop patch application."
        )

    # ======================================
    # CHECK TARGET PATH
    # ======================================

    workspace = Path("workspace").resolve()
    target = Path(file_path).resolve()

    # Ensure target is inside workspace
    if not target.is_relative_to(workspace):

        return finish_patch(
            success=False,
            result="Target file must be inside workspace.",

            thought=(
                "The requested target is outside the allowed "
                "workspace directory."
            ),

            action="Reject unsafe target path."
        )

    if not target.is_file():

        return finish_patch(
            success=False,
            result="Target file does not exist.",

            thought=(
                "The target source file does not exist. "
                "There is no file available to patch."
            ),

            action="Stop patch application."
        )

    # ======================================
    # WRITE PATCH
    # ======================================

    try:

        target.write_text(
            fixed_code,
            encoding="utf-8"
        )

        result = f"Patch successfully applied to {target}"

        print(result)

        return finish_patch(
            success=True,
            result=result,

            thought=(
                "The patch was approved and the target file "
                "passed workspace safety checks."
            ),

            action=f"Write fixed code to {target}."
        )

    except OSError as error:

        return finish_patch(
            success=False,
            result=f"Failed to apply patch: {error}",

            thought=(
                "The patch could not be written because "
                "a file system error occurred."
            ),

            action="Attempt to write fixed code; operation failed."
        )


# ==========================================
# 3. VALIDATION ROUTER
# ==========================================

def route_after_validation(state: AgentState) -> str:

    validation_status = state.get("validation_status")

    print("\n========== VALIDATION ROUTER ==========")
    print("Validation status:", validation_status)

    if validation_status == "VALID":
        print("Next step: apply_patch")
        return "apply_patch"

    print("Next step: END")
    return END


# ==========================================
# 4. BUILD LANGGRAPH
# ==========================================

builder = StateGraph(AgentState)

builder.add_node("syntax_checker", syntax_checker_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("rag_specialist", rag_specialist_node)
builder.add_node("code_fixer", code_fixer_node)
builder.add_node("validation", validation_node)
builder.add_node("apply_patch", apply_patch_node)


# ==========================================
# 5. DEFINE GRAPH EDGES
# ==========================================

# Initial diagnosis
builder.add_edge(START, "syntax_checker")

builder.add_edge("syntax_checker", "supervisor")

# Supervisor controls worker selection
builder.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "rag_specialist": "rag_specialist",
        "code_fixer": "code_fixer",
        "validation": "validation",
        "END": END
    }
)

# RAG returns its result to Supervisor
builder.add_edge("rag_specialist", "supervisor")

# Code Fixer returns generated code to Supervisor
builder.add_edge("code_fixer", "supervisor")

# Validate generated code
builder.add_conditional_edges(
    "validation",
    route_after_validation,
    {
        "apply_patch": "apply_patch",
        END: END
    }
)

# Finish after patch application
builder.add_edge("apply_patch", END)


# ==========================================
# 6. CHECKPOINTER + HUMAN-IN-THE-LOOP
# ==========================================

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["apply_patch"]
)
