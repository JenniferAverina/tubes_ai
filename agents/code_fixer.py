
# agents/code_fixer.py

import os
import re

from langchain_ollama import ChatOllama

from state import AgentState


# ==========================================
# 1. INITIALIZE LOCAL LLM
# ==========================================

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)

FIXED_CODE_PREVIEW_PATH = "./workspace/fixed_code.py"


# ==========================================
# 2. CLEAN LLM OUTPUT
# ==========================================

def clean_code_output(raw_text: str) -> str:

    pattern = r"```(?:python)?\s*(.*?)```"

    match = re.search(
        pattern,
        raw_text,
        re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return raw_text.strip()


# ==========================================
# 3. CODE FIXER NODE
# ==========================================

def code_fixer_node(state: AgentState) -> dict:

    print("\n========== CODE FIXER START ==========")

    source_code = state.get("source_code", "")

    diagnosis = state.get("diagnosis") or {}

    knowledge = state.get(
        "knowledge_result",
        "NOT_FOUND"
    )

    fix_attempts = state.get("fix_attempts", 0)

    trace = list(state.get("react_trace", []))

    # ======================================
    # 4. READ DIAGNOSIS
    # ======================================

    error_type = diagnosis.get(
        "error_type",
        "UnknownError"
    )

    error_message = diagnosis.get(
        "error_message",
        ""
    )

    line = diagnosis.get(
        "line",
        "Unknown"
    )

    column = diagnosis.get("column")

    source_line = diagnosis.get(
        "source_line",
        ""
    )

    location_detail = (
        f"Line {line}"
        + (f", Column {column}" if column is not None else "")
    )

    print("Error Type:", error_type)
    print("Error Message:", error_message)
    print("Location:", location_detail)

    # ======================================
    # 5. PREPARE KNOWLEDGE CONTEXT
    # ======================================

    if knowledge and knowledge != "NOT_FOUND":

        kb_context = knowledge

        print("\nKnowledge Base: FOUND")

    else:

        kb_context = (
            "No specific Knowledge Base entry found. "
            "Apply standard Python debugging best practices."
        )

        print("\nKnowledge Base: NOT_FOUND")
        print("Using debugging best practices fallback.")

    # ======================================
    # 6. CONSTRUCT REPAIR PROMPT
    # ======================================

    prompt = f"""
You are an expert Python Automated Code Fixer.

Your task is to fix the bug in the provided Python source code.

ORIGINAL BUGGY CODE:

```python
{source_code}
```

DIAGNOSTIC REPORT:

Error Type: {error_type}
Error Message: {error_message}
Location: {location_detail}
Offending Line: {source_line if source_line else "N/A"}

KNOWLEDGE BASE SOLUTION:

{kb_context}

INSTRUCTIONS:

1. Fix the identified error.
2. Preserve the original program's intended logic.
3. Preserve function signatures and variable names when possible.
4. Return ONLY complete, valid, runnable Python code.
5. Do not include explanations or conversational text.
"""

    # ======================================
    # 7. INVOKE QWEN
    # ======================================

    print("\n[CODE FIXER] Asking Qwen to generate fix...")

    response = llm.invoke(prompt)

    fixed_code = clean_code_output(response.content)

    print("\n========== GENERATED FIX ==========")
    print(fixed_code)

    # ======================================
    # 8. VALIDATE OUTPUT
    # ======================================

    if not fixed_code.strip():

        print("ERROR: Code Fixer returned empty code.")

        return {
            "fixed_code": "",
            "fix_attempts": fix_attempts + 1,
            "react_trace": trace
        }

    # ======================================
    # 9. SAVE PREVIEW
    # ======================================

    os.makedirs(
        os.path.dirname(FIXED_CODE_PREVIEW_PATH),
        exist_ok=True
    )

    with open(
        FIXED_CODE_PREVIEW_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(fixed_code + "\n")

    print("\nPreview saved to:", FIXED_CODE_PREVIEW_PATH)

    # ======================================
    # 10. REACT TRACE
    # ======================================

    trace.append({

        "agent": "code_fixer",

        "attempt": fix_attempts + 1,

        "thought": (
            f"Synthesizing code repair for {error_type} "
            f"at {location_detail}. "
            f"Knowledge Base status: "
            f"{'FOUND' if knowledge != 'NOT_FOUND' else 'NOT_FOUND'}."
        ),

        "action": (
            "Invoke ChatOllama (qwen2.5:7b) "
            "to generate patched code."
        ),

        "observation": (
            f"Generated {len(fixed_code.splitlines())} "
            f"lines of corrected Python code."
        )
    })

    # ======================================
    # 11. RETURN UPDATED STATE
    # ======================================

    return {

        "fixed_code": fixed_code,

        "fix_attempts": fix_attempts + 1,

        "react_trace": trace
    }
