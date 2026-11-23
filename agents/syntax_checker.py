
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

from tools.syntax_tool import check_syntax
from tools.execution_tool import execute_code
from tools.trace_logger import log_trace
from state import AgentState


# ==========================================
# 1. INITIALIZE LOCAL LLM
# ==========================================

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)


# ==========================================
# 2. DEFINE AVAILABLE TOOLS
# ==========================================

@tool
def syntax_checker_tool(source_code: str) -> str:
    """Memeriksa syntax error pada source code Python."""

    result = check_syntax(source_code)

    return json.dumps(result, ensure_ascii=False)


@tool
def execution_tool(source_code: str) -> str:
    """Menjalankan source code Python untuk mendeteksi runtime error. Hanya gunakan setelah syntax valid."""

    result = execute_code(source_code)

    return json.dumps(result, ensure_ascii=False)


tools = {
    "syntax_checker_tool": syntax_checker_tool,
    "execution_tool": execution_tool
}

llm_with_tools = llm.bind_tools(
    [syntax_checker_tool, execution_tool]
)


# ==========================================
# 3. REACT SYNTAX CHECKER WORKER
# ==========================================

def syntax_checker_node(state: AgentState) -> dict:

    source_code = state.get("source_code", "")
    react_trace = list(state.get("react_trace", []))

    # ======================================
    # EMPTY INPUT HANDLING
    # ======================================

    if not source_code.strip():

        diagnosis = {
            "status": "ERROR",
            "error_type": "EmptyInput",
            "error_message": "Source code is empty.",
            "line": None
        }

        trace = log_trace(
            agent="SYNTAX_CHECKER",
            thought="Source code kosong sehingga proses diagnosis tidak dapat dilanjutkan.",
            action="Check source code input",
            observation=diagnosis
        )

        react_trace.append(trace)

        return {
            "syntax_result": None,
            "execution_result": None,
            "diagnosis": diagnosis,
            "react_trace": react_trace
        }

    print("\n========== REACT AGENT START ==========")

    messages = [
        (
            "system",
            """
            You are a Python Code Diagnostic Agent.

            Your task is to diagnose Python code using available tools.

            Follow these rules:

            1. Always call syntax_checker_tool first.
            2. If syntax checking finds an error, do not call execution_tool.
            3. If syntax is valid, call execution_tool.
            4. Observe the tool results before deciding the next action.
            5. Do not claim a tool was executed if it was not.
            6. Finish after the diagnosis is complete.

            Use tools to perform actual code analysis.
            """
        ),
        (
            "human",
            f"Please diagnose this Python code:\n\n{source_code}"
        )
    ]

    syntax_result = None
    execution_result = None

    # ======================================
    # 4. REACT LOOP: THOUGHT-ACTION-OBSERVATION
    # ======================================

    for step in range(4):

        print(f"\n========== REACT STEP {step + 1} ==========")

        response = llm_with_tools.invoke(messages)

        messages.append(response)

        # LLM tidak meminta tool tambahan
        if not response.tool_calls:

            trace = log_trace(
                agent="SYNTAX_CHECKER",
                thought="Agent mengevaluasi apakah pemeriksaan yang diperlukan sudah selesai.",
                action="Stop ReAct loop",
                observation="Qwen tidak meminta tool tambahan."
            )

            react_trace.append(trace)
            break

        for call in response.tool_calls:

            tool_name = call["name"]

            # ======================================
            # SYNTAX TOOL
            # ======================================

            if tool_name == "syntax_checker_tool":

                thought = (
                    "Agent harus memeriksa syntax Python terlebih dahulu "
                    "sebelum menjalankan kode."
                )

                action = "Execute syntax_checker_tool"

                if syntax_result is not None:

                    result = "Syntax Tool sudah pernah dijalankan."

                else:

                    raw_result = syntax_checker_tool.invoke(
                        call["args"]
                    )

                    syntax_result = json.loads(raw_result)

                    result = raw_result

                trace = log_trace(
                    agent="SYNTAX_CHECKER",
                    thought=thought,
                    action=action,
                    observation=result
                )

                react_trace.append(trace)

            # ======================================
            # EXECUTION TOOL
            # ======================================

            elif tool_name == "execution_tool":

                thought = (
                    "Agent mengevaluasi hasil syntax checking. "
                    "Execution hanya diperbolehkan jika syntax valid."
                )

                action = "Execute execution_tool"

                if syntax_result is None:

                    result = (
                        "Execution ditolak. "
                        "Syntax Tool harus dijalankan terlebih dahulu."
                    )

                elif syntax_result["has_error"]:

                    result = (
                        "Execution tidak dijalankan karena "
                        "Syntax Error ditemukan."
                    )

                elif execution_result is not None:

                    result = "Execution Tool sudah pernah dijalankan."

                else:

                    raw_result = execution_tool.invoke(
                        call["args"]
                    )

                    execution_result = json.loads(raw_result)

                    result = raw_result

                trace = log_trace(
                    agent="SYNTAX_CHECKER",
                    thought=thought,
                    action=action,
                    observation=result
                )

                react_trace.append(trace)

            # ======================================
            # UNKNOWN TOOL
            # ======================================

            else:

                result = f"Tool tidak tersedia: {tool_name}"

                trace = log_trace(
                    agent="SYNTAX_CHECKER",
                    thought="Agent menerima permintaan tool yang tidak terdaftar.",
                    action=f"Reject tool: {tool_name}",
                    observation=result
                )

                react_trace.append(trace)

            # Kirim hasil tool kembali ke LLM
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"]
                )
            )

        # Hentikan jika syntax error ditemukan
        if syntax_result is not None and syntax_result["has_error"]:
            break

        # Hentikan jika kedua pemeriksaan selesai
        if syntax_result is not None and execution_result is not None:
            break

    # ==========================================
    # 5. GENERATE FINAL DIAGNOSIS
    # ==========================================

    print("\n========== FINAL DIAGNOSIS ==========")

    if syntax_result is None:

        diagnosis = {
            "status": "ERROR",
            "error_type": "DiagnosticIncomplete",
            "error_message": "Syntax Tool was not executed.",
            "line": None
        }

    elif syntax_result["has_error"]:

        diagnosis = {
            "status": "ERROR",
            "error_type": syntax_result["error_type"],
            "error_message": syntax_result["error_message"],
            "line": syntax_result["line"],
            "column": syntax_result["column"],
            "source_line": syntax_result["source_line"]
        }

    elif execution_result is None:

        diagnosis = {
            "status": "ERROR",
            "error_type": "DiagnosticIncomplete",
            "error_message": "Execution Tool was not executed.",
            "line": None
        }

    elif execution_result["has_error"]:

        diagnosis = {
            "status": "ERROR",
            "error_type": execution_result["error_type"],
            "error_message": execution_result["error_message"],
            "line": execution_result["line"]
        }

    else:

        diagnosis = {
            "status": "SUCCESS",
            "error_type": None,
            "error_message": None,
            "line": None
        }

    # Log final diagnosis
    trace = log_trace(
        agent="SYNTAX_CHECKER",
        thought="Agent menyimpulkan hasil diagnosis berdasarkan hasil Syntax Tool dan Execution Tool.",
        action="Generate final diagnosis",
        observation=diagnosis
    )

    react_trace.append(trace)

    return {
        "syntax_result": syntax_result,
        "execution_result": execution_result,
        "diagnosis": diagnosis,
        "react_trace": react_trace
    }


# ==========================================
# 6. TESTING
# ==========================================

if __name__ == "__main__":

    test_state = {
        "source_code": """
angka = 10
hasil = angka / 0

print(hasil)
""",
        "react_trace": []
    }

    result = syntax_checker_node(test_state)

    print("\n========== WORKER RESULT ==========")

    for key, value in result.items():

        print(f"\n{key}:")
        print(value)
