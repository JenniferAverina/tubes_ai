# agents/code_fixer.py
import os
import re
from langchain_ollama import ChatOllama
from state import AgentState

# Initialize local Ollama LLM
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

# Path assigned to Member 2 for staging the proposed fix before human approval
FIXED_CODE_PREVIEW_PATH = "./workspace/fixed_code.py"


def clean_code_output(raw_text: str) -> str:
    """Extracts pure Python code if the LLM wraps its response in markdown backticks."""
    pattern = r"```(?:python)?\s*(.*?)```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def code_fixer_node(state: AgentState) -> AgentState:
    """
    Worker node for Member 2: Repairs buggy Python code using diagnosis + RAG knowledge.
    Reads from and writes to the shared AgentState.
    """
    # 1. Read existing values from shared AgentState
    source_code = state.get("source_code", "")
    diagnosis = state.get("diagnosis") or {}
    knowledge = state.get("knowledge_result", "NOT_FOUND")
    fix_attempts = state.get("fix_attempts", 0)
    trace = list(state.get("react_trace", []))

    # Extract Member 1's diagnostic details safely using .get()
    error_type = diagnosis.get("error_type", "UnknownError")
    error_message = diagnosis.get("error_message", "")
    line = diagnosis.get("line", "Unknown")
    column = diagnosis.get("column")
    source_line = diagnosis.get("source_line", "")

    # Format optional syntax-specific details if present
    location_detail = f"Line {line}" + (f", Column {column}" if column is not None else "")
    kb_context = (
        knowledge
        if knowledge and knowledge != "NOT_FOUND"
        else "No specific Knowledge Base entry found. Apply standard Python debugging best practices."
    )

    # 2. Construct the repair prompt for Qwen 2.5 7B
    prompt = f"""You are an expert Python Automated Code Fixer.
Your task is to fix the bug in the provided Python source code based on the diagnostic report and knowledge base recommendations.

### ORIGINAL BUGGY CODE:
```python
{source_code}
```

### DIAGNOSTIC REPORT:
- Error Type: {error_type}
- Error Message: {error_message}
- Location: {location_detail}
- Offending Line: {source_line if source_line else "N/A (Runtime Error)"}

### KNOWLEDGE BASE SOLUTION:
{kb_context}

### INSTRUCTIONS:
1. Fix the identified error while preserving the original program's intended logic, function signatures, and variable names.
2. Return ONLY the complete, valid, runnable Python code.
3. Do NOT include markdown explanations, conversational text, or notes outside the code block.
"""

    # 3. Invoke local LLM and strip any markdown code fences
    response = llm.invoke(prompt)
    fixed_code = clean_code_output(response.content)

    # 4. Save preview to workspace/fixed_code.py (leaves workspace/buggy_code.py untouched until approval)
    os.makedirs(os.path.dirname(FIXED_CODE_PREVIEW_PATH), exist_ok=True)
    with open(FIXED_CODE_PREVIEW_PATH, "w", encoding="utf-8") as f:
        f.write(fixed_code + "\n")

    # 5. Record ReAct trace step
    trace.append({
        "agent": "code_fixer",
        "attempt": fix_attempts + 1,
        "thought": (
            f"Synthesizing code repair for {error_type} at {location_detail}. "
            f"Knowledge Base status: {'FOUND' if knowledge != 'NOT_FOUND' else 'NOT_FOUND'}."
        ),
        "action": "Invoke ChatOllama (qwen2.5:7b) to generate patched code and save preview to workspace/fixed_code.py",
        "observation": f"Generated {len(fixed_code.splitlines())} lines of corrected Python code."
    })

    # 6. Return updated state fields
    return {
        "fixed_code": fixed_code,
        "fix_attempts": fix_attempts + 1,
        "react_trace": trace
    }