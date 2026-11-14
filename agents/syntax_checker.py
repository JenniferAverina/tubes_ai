import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

from tools.syntax_tool import check_syntax
from tools.execution_tool import execute_code
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

    if not source_code.strip():
        return {
            "syntax_result": None,
            "execution_result": None,
            "react_trace": [],
            "diagnosis": {
                "status": "ERROR",
                "error_type": "EmptyInput",
                "error_message": "Source code is empty.",
                "line": None
            }
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
    react_trace = []

    # ======================================
    # 4. REACT LOOP: THOUGHT-ACTION-OBSERVATION
    # ======================================
    for step in range(4):

        print(f"\n========== REACT STEP {step + 1} ==========")

        print("[THOUGHT] Qwen sedang menentukan tindakan berikutnya.")

        response = llm_with_tools.invoke(messages)

        messages.append(response)

        if not response.tool_calls:
            print("[OBSERVATION] Qwen tidak meminta tool tambahan.")
            break

        for call in response.tool_calls:

            tool_name = call["name"]

            print(f"\n[ACTION] Qwen memilih: {tool_name}")
            react_trace.append({
            "step": step + 1,
            "action": tool_name
            })

            # SYNTAX TOOL
            if tool_name == "syntax_checker_tool":

                if syntax_result is not None:
                    result = "Syntax Tool sudah pernah dijalankan."
                else:
                    raw_result = syntax_checker_tool.invoke(
                        call["args"]
                    )

                    syntax_result = json.loads(raw_result)

                    result = raw_result

                print("[OBSERVATION]", result)
                react_trace[-1]["observation"] = result

            # EXECUTION TOOL
            elif tool_name == "execution_tool":

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

                print("[OBSERVATION]", result)
                react_trace[-1]["observation"] = result

            else:
                result = "Tool tidak tersedia."

                print("[OBSERVATION]", result)
                react_trace[-1]["observation"] = result

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"]
                )
            )

        # Hentikan jika syntax error sudah ditemukan.
        if syntax_result is not None and syntax_result["has_error"]:
            break

        # Hentikan jika kedua pemeriksaan sudah selesai.
        if syntax_result is not None and execution_result is not None:
            break

    # ======================================
    # 5. GENERATE FINAL DIAGNOSIS
    # ======================================
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

    print("[OBSERVATION]", diagnosis)
    react_trace.append({
    "step": "final",
    "action": "generate_diagnosis",
    "observation": diagnosis
    })

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
"""
    }
    result = syntax_checker_node(test_state)

    print("\n========== WORKER RESULT ==========")

    for key, value in result.items():
        print(f"\n{key}:")
        print(value)
